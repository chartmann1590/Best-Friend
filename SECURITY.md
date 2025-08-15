# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

1. **Do not create a public GitHub issue** for security vulnerabilities
2. **Email us directly** at security@bestfriend.local (replace with actual email)
3. **Include detailed information** about the vulnerability
4. **Allow us time** to investigate and respond

### What to Include

When reporting a vulnerability, please provide:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 1 week
- **Resolution**: As soon as possible, typically within 30 days

## Security Features

### Authentication & Authorization

- **Password Security**: bcrypt hashing with salt
- **Session Management**: Secure HTTP-only cookies
- **CSRF Protection**: Token-based protection on all forms
- **Rate Limiting**: Per-IP and per-user limits

### Data Protection

- **Encryption**: Fernet encryption for sensitive settings
- **Database Security**: PostgreSQL with pgvector
- **Input Validation**: Comprehensive validation on all inputs
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

### Network Security

- **HTTPS Only**: TLS 1.2+ with secure ciphers
- **Security Headers**: CSP, HSTS, XSS protection
- **Reverse Proxy**: Nginx with strict security configuration
- **CORS**: Properly configured for API endpoints

### Privacy Controls

- **Data Export**: Full user data export capability
- **Data Deletion**: Complete data removal on request
- **Memory Toggle**: User control over memory features
- **Local Deployment**: All data stays on user's infrastructure

## Security Best Practices

### For Users

1. **Change Default Credentials**: Update admin password immediately
2. **Use Strong Passwords**: Minimum 8 characters, mix of types
3. **Keep Updated**: Regularly update the application
4. **Monitor Logs**: Check for suspicious activity
5. **Backup Data**: Regular database backups
6. **Network Security**: Use firewall and VPN if needed

### For Administrators

1. **Environment Variables**: Use strong, unique keys
2. **SSL Certificates**: Use valid certificates in production
3. **Access Control**: Limit admin access
4. **Monitoring**: Set up logging and alerting
5. **Updates**: Keep dependencies updated
6. **Backups**: Regular automated backups

## Known Issues

None currently known.

## Security Updates

Security updates will be released as patch versions (1.0.1, 1.0.2, etc.) and announced via:

- GitHub releases
- Security advisories
- Email notifications (if subscribed)

## Compliance

This application is designed to be compliant with:

- **GDPR**: Data export/deletion capabilities
- **CCPA**: Privacy controls and data rights
- **SOC 2**: Security controls and monitoring
- **OWASP Top 10**: Protection against common vulnerabilities

## Contact

For security-related questions or reports:

- **Email**: security@bestfriend.local
- **PGP Key**: [Add if available]
- **Response Time**: 48 hours for initial response
