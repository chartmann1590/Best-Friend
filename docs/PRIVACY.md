# Privacy Policy

This document outlines the privacy practices for the Best Friend AI Companion application.

## Data Collection

### What We Collect
- **User Profile**: Name, email, timezone, bio, preferences
- **Conversations**: Chat messages between users and AI
- **Voice Data**: Audio recordings for speech-to-text processing
- **Settings**: AI configuration, voice preferences, memory settings
- **Usage Data**: Login times, feature usage, system interactions

### What We Don't Collect
- **Personal Identifiers**: Social security numbers, driver's license numbers
- **Financial Information**: Credit card numbers, bank account details
- **Location Data**: GPS coordinates, precise location information
- **Biometric Data**: Fingerprints, facial recognition data

## Data Storage

### Database Storage
- **User Data**: Stored in PostgreSQL with encryption for sensitive fields
- **Conversations**: Stored with user association and timestamps
- **Memories**: Vector embeddings stored in pgvector for similarity search
- **Settings**: User preferences and configuration stored securely

### Encryption
- **At Rest**: Sensitive data encrypted using Fernet symmetric encryption
- **In Transit**: All data transmitted over HTTPS/TLS
- **Keys**: Encryption keys stored in environment variables, not in code

### Data Retention
- **Active Users**: Data retained while account is active
- **Inactive Users**: Data retained for 1 year after last login
- **Deleted Users**: Data permanently removed within 30 days
- **Backups**: Encrypted backups retained for 90 days

## Data Usage

### Primary Purpose
- **AI Companion**: Provide personalized AI chat experience
- **Memory System**: Remember user preferences and conversation context
- **Voice Interface**: Enable speech-to-text and text-to-speech features
- **Personalization**: Customize AI responses based on user profile

### Internal Use
- **Service Improvement**: Analyze usage patterns to improve features
- **Bug Fixes**: Identify and resolve technical issues
- **Performance**: Monitor system performance and optimize resources
- **Security**: Detect and prevent security threats

### Third-Party Services
- **Ollama**: AI model processing (no data shared)
- **OpenTTS/Piper**: Text-to-speech conversion (no data stored)
- **faster-whisper**: Speech-to-text processing (no data stored)

## User Control

### Data Access
- **Profile**: View and edit personal information
- **Conversations**: Access complete chat history
- **Memories**: View stored memories and their relevance scores
- **Settings**: Modify AI and voice configuration

### Data Export
- **Format**: JSON export of all user data
- **Content**: Profile, conversations, memories, settings
- **Access**: Available via `/api/export` endpoint
- **Timing**: Export processed within 24 hours

### Data Deletion
- **Account Deletion**: Remove all user data permanently
- **Selective Deletion**: Delete specific conversations or memories
- **Process**: Data marked for deletion and removed within 30 days
- **Confirmation**: Email confirmation required for account deletion

### Memory Control
- **Enable/Disable**: Toggle memory system on/off
- **Retention**: Set custom memory retention periods
- **Types**: Control which types of memories are stored
- **Importance**: Adjust memory importance scoring

## Security Measures

### Access Control
- **Authentication**: Password-based login with bcrypt hashing
- **Sessions**: Secure session management with Redis
- **Authorization**: Role-based access control (user/admin)
- **Rate Limiting**: Prevent abuse and brute force attacks

### Data Protection
- **Encryption**: Sensitive data encrypted at rest
- **Isolation**: User data isolated by user ID
- **Backups**: Encrypted backups with access controls
- **Audit Logs**: Track data access and modifications

### Network Security
- **HTTPS**: All communication encrypted with TLS
- **Headers**: Security headers prevent common attacks
- **CSP**: Content Security Policy blocks malicious content
- **Firewall**: Network-level access controls

## Compliance

### GDPR Compliance
- **Right to Access**: Users can request their data
- **Right to Rectification**: Users can correct inaccurate data
- **Right to Erasure**: Users can delete their data
- **Right to Portability**: Users can export their data
- **Data Processing**: Legal basis for data processing documented

### CCPA Compliance
- **Right to Know**: Users informed about data collection
- **Right to Delete**: Users can request data deletion
- **Right to Opt-Out**: Users can opt out of data sharing
- **Non-Discrimination**: No discrimination for privacy choices

### COPPA Compliance
- **Age Verification**: Users must be 13+ to use service
- **Parental Consent**: Required for users under 13
- **Limited Collection**: Minimal data collection for minors
- **Parental Rights**: Parents can review and delete child data

## Data Sharing

### No Sale of Data
- **Personal Information**: Never sold to third parties
- **Usage Data**: Never sold for advertising purposes
- **Conversations**: Never shared with external parties
- **Preferences**: Never used for targeted advertising

### Legal Requirements
- **Law Enforcement**: Data shared only with valid legal requests
- **Court Orders**: Compliance with subpoenas and court orders
- **Emergency**: Data shared in emergency situations
- **Documentation**: All legal requests documented and logged

### Service Providers
- **Hosting**: Data hosted on secure cloud infrastructure
- **Processing**: AI processing through Ollama integration
- **Storage**: Database and file storage on secure servers
- **Monitoring**: System monitoring for performance and security

## User Rights

### Information Rights
- **Transparency**: Clear information about data practices
- **Updates**: Notification of privacy policy changes
- **Contact**: Multiple ways to contact privacy team
- **Complaints**: Process for privacy-related complaints

### Control Rights
- **Consent**: Withdraw consent for data processing
- **Restriction**: Limit how data is processed
- **Portability**: Transfer data to other services
- **Objection**: Object to specific data processing

### Redress Rights
- **Complaints**: File complaints with privacy team
- **Appeals**: Appeal decisions about data requests
- **Compensation**: Seek compensation for privacy violations
- **Legal Action**: Pursue legal remedies if necessary

## Data Breach Response

### Detection
- **Monitoring**: Continuous monitoring for security threats
- **Alerts**: Automated alerts for suspicious activity
- **Investigation**: Immediate investigation of potential breaches
- **Assessment**: Impact assessment within 72 hours

### Notification
- **Users**: Notify affected users within 72 hours
- **Authorities**: Report to relevant authorities as required
- **Public**: Public disclosure if required by law
- **Updates**: Regular updates on breach response

### Remediation
- **Containment**: Immediate containment of breach
- **Investigation**: Thorough investigation of cause
- **Fixes**: Implementation of security fixes
- **Prevention**: Measures to prevent future breaches

## Privacy by Design

### Default Settings
- **Minimal Collection**: Only necessary data collected
- **Privacy First**: Privacy-friendly default settings
- **User Choice**: Users must opt-in to additional features
- **Transparency**: Clear information about data use

### Technical Measures
- **Encryption**: Data encrypted by default
- **Access Controls**: Strict access controls implemented
- **Audit Logs**: Comprehensive logging of data access
- **Regular Reviews**: Privacy impact assessments conducted

### User Education
- **Privacy Guide**: Comprehensive privacy documentation
- **Best Practices**: Tips for protecting personal information
- **Settings Guide**: Explanation of privacy settings
- **FAQ**: Common privacy questions and answers

## Contact Information

### Privacy Team
- **Email**: privacy@bestfriend.local
- **Phone**: +1-555-PRIVACY
- **Address**: Privacy Team, Best Friend AI Companion

### Response Times
- **General Inquiries**: 48 hours
- **Data Requests**: 30 days
- **Breach Reports**: 72 hours
- **Complaints**: 14 days

### Escalation
- **Privacy Officer**: Direct escalation for complex issues
- **Legal Team**: Legal review for compliance issues
- **External Mediation**: Third-party mediation if needed
- **Regulatory Bodies**: Contact relevant authorities

## Updates and Changes

### Policy Updates
- **Notification**: Users notified of policy changes
- **Review Period**: 30-day review period for major changes
- **Consent**: New consent required for significant changes
- **Documentation**: All changes documented and archived

### Version History
- **Current Version**: 1.0 (Effective: January 1, 2024)
- **Previous Versions**: Available upon request
- **Change Log**: Summary of all policy changes
- **Archive**: Complete policy history maintained

### User Communication
- **Email Notifications**: Direct email for important changes
- **In-App Notifications**: App notifications for updates
- **Website Updates**: Policy posted on website
- **Social Media**: Announcements on social platforms
