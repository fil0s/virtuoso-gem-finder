# Security Guidelines

## Environment Configuration

### Setup
1. Copy `.env.template` to `.env`
2. Fill in your actual API keys and tokens
3. Never commit `.env` files to version control

### API Key Security
- **Birdeye API Key**: Required for token data fetching
- **Moralis API Key**: Required for blockchain data access  
- **Helius API Key**: Required for Solana network access
- **Telegram Bot Token**: Optional, for notifications

### Best Practices
- Rotate API keys regularly
- Use environment-specific .env files (.env.production, .env.development)
- Monitor for exposed credentials using GitGuardian or similar tools
- Never hardcode secrets in source code

### Exposed Credentials Response
If credentials are accidentally exposed:
1. Immediately rotate the exposed keys/tokens
2. Remove from git history using `git filter-branch`
3. Update `.gitignore` to prevent future exposure
4. Scan repository for other potential leaks

### File Exclusions
The following files are excluded from version control for security:
- `.env*` (except templates)
- `*.key`, `*.pem` files
- `*_credentials.json`
- Log files that may contain sensitive data
- Test results with API responses

## Reporting Security Issues
Report security vulnerabilities privately to the repository maintainer.