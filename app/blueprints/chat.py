from flask import Blueprint, request, jsonify, Response, stream_template, current_app
from flask_login import login_required, current_user
from app import db, limiter
from app.models import Message, Memory
from app.logging_config import log_ai_interaction, log_content_filter_event, log_error, log_performance
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest
import json
import time

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
@login_required
@limiter.limit("50 per minute")
def chat():
    """Handle chat messages."""
    start_time = time.time()
    
    try:
        # Validate CSRF token from headers (for AJAX requests)
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            return jsonify({'error': 'CSRF token missing'}), 400
        
        try:
            validate_csrf(csrf_token)
        except BadRequest:
            return jsonify({'error': 'CSRF token validation failed'}), 400
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Content filtering
        content_filter = current_app.content_filter
        filter_result = content_filter.filter_content(message, current_user.id)
        
        # Log content filter result
        log_content_filter_event(
            current_user.id, 
            message[:100] + "..." if len(message) > 100 else message, 
            filter_result
        )
        
        if filter_result['blocked']:
            log_error(
                Exception("Content blocked"), 
                f"User {current_user.id} attempted to send blocked content"
            )
            return jsonify({
                'error': 'Content blocked for safety',
                'reason': filter_result['blocked_reason']
            }), 400
        
        # Save user message
        user_message = Message(
            user_id=current_user.id,
            role='user',
            content=message
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Generate AI response using Ollama
        prompt_service = current_app.prompt_service
        system_prompt = prompt_service.build_chat_prompt(current_user.id, message)
        
        # Get AI response from Ollama
        ollama_client = current_app.ollama_client
        ai_response = ollama_client.generate_response(system_prompt)
        
        # Create memory from this conversation turn
        if current_app.memory_service:
            current_app.memory_service.create_conversation_memory(
                current_user.id, 
                [user_message]
            )
        
        # Save AI response
        assistant_message = Message(
            user_id=current_user.id,
            role='assistant',
            content=ai_response
        )
        db.session.add(assistant_message)
        db.session.commit()
        
        # Log AI interaction
        log_ai_interaction(
            'chat_completion',
            current_user.id,
            f"Message length: {len(message)}, Response length: {len(ai_response)}"
        )
        
        # Log performance
        duration = time.time() - start_time
        log_performance('chat_request', duration, f"User: {current_user.id}")
        
        return jsonify({
            'response': ai_response,
            'message_id': assistant_message.id
        })
        
    except Exception as e:
        log_error(e, f"Chat endpoint error for user {current_user.id}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/stt', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def speech_to_text():
    """Convert speech to text."""
    # Validate CSRF token from headers (for AJAX requests)
    csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
    if not csrf_token:
        return jsonify({'error': 'CSRF token missing'}), 400
    
    try:
        validate_csrf(csrf_token)
    except BadRequest:
        return jsonify({'error': 'CSRF token validation failed'}), 400
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    # Process audio with STT service
    stt_service = current_app.stt_service
    result = stt_service.transcribe_audio(audio_file)
    
    if result['success']:
        transcribed_text = result['text']
        confidence = result['confidence']
    else:
        transcribed_text = f"Transcription failed: {result.get('error', 'Unknown error')}"
        confidence = 0.0
    
    return jsonify({
        'text': transcribed_text,
        'confidence': 0.95
    })

@chat_bp.route('/tts/stream')
@login_required
@limiter.limit("100 per minute")
def text_to_speech_stream():
    """Stream TTS audio."""
    text = request.args.get('text', '')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    # Generate speech using TTS service
    tts_service = current_app.tts_service
    audio_data = tts_service.synthesize_speech(text)
    
    if audio_data:
        # Return audio data as response
        from flask import Response
        return Response(
            audio_data,
            mimetype='audio/wav',
            headers={'Content-Disposition': 'attachment; filename=speech.wav'}
        )
    else:
        return jsonify({'error': 'Failed to generate speech'}), 500

@chat_bp.route('/memory/search')
@login_required
def search_memories():
    """Search user memories."""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Search memories using vector similarity
    memory_service = current_app.memory_service
    memory_results = memory_service.search_memories(
        user_id=current_user.id,
        query=query,
        limit=10,
        threshold=0.5
    )
    
    # Format results
    memories = []
    for memory, similarity in memory_results:
        memories.append({
            'id': memory.id,
            'content': memory.content,
            'memory_type': memory.memory_type,
            'relevance': similarity,
            'created_at': memory.created_at.isoformat() if memory.created_at else None
        })
    
    return jsonify({
        'memories': memories,
        'query': query
    })
