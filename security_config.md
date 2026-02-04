# MitsuList Security Configuration Guide

This document explains the security features implemented in the MitsuList application.

## 🔒 Security Features Overview

### 1. Rate Limiting
Protects the application from abuse and excessive API calls to the Jikan API.

**Implementation**: `django-ratelimit` package

**Rate Limits by Endpoint**:
- **Homepage** (`/`): 20 requests per minute per IP
- **Anime Detail** (`/anime/id=<id>`): 60 requests per minute per IP  
- **Search API** (`/api-proxy/<query>`): 30 requests per minute per IP

**How It Works**:
- Tracks requests by IP address
- Returns HTTP 429 (Too Many Requests) when limit exceeded
- Limits reset every minute
- Uses Django cache backend for tracking

**Configuration** (in `settings.py`):
```python
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
```

**Adjusting Limits**:
Edit the decorators in `app/views.py`:
```python
@ratelimit(key='ip', rate='30/m', method='GET', block=True)  # 30 per minute
```

---

### 2. Content Security Policy (CSP)
Protects against Cross-Site Scripting (XSS) and code injection attacks.

**Implementation**: `django-csp` package

**Allowed Sources**:
- **Scripts**: Same origin + Font Awesome CDN
- **Styles**: Same origin + Google Fonts + Font Awesome (with inline styles)
- **Fonts**: Same origin + Google Fonts CDN + Font Awesome
- **Images**: HTTPS sources (for anime posters) + data URIs
- **Connections**: Same origin + Jikan API (`api.jikan.moe`)
- **Frames**: Blocked (none)
- **Objects**: Blocked (none)

**Configuration** (in `settings.py`):
```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", 'https://cdnjs.cloudflare.com')
CSP_IMG_SRC = ("'self'", 'https:', 'data:')
# ... more directives
```

**Browser Response**:
If a resource violates CSP policy, the browser will block it and log a violation in the console.

---

### 3. HTTPS & Security Headers

#### HTTPS Redirect (Production Only)
Automatically redirects all HTTP requests to HTTPS when `DEBUG=False`.

**Configuration**:
```python
SECURE_SSL_REDIRECT = not DEBUG  # Only in production
```

#### HTTP Strict Transport Security (HSTS)
Forces browsers to only connect via HTTPS for 1 year.

**Configuration**:
```python
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

**Important**: Only enabled in production (`DEBUG=False`)

#### Secure Cookies
Ensures cookies are only sent over HTTPS in production.

**Configuration**:
```python
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True  # Prevents JavaScript access
CSRF_COOKIE_HTTPONLY = True
```

#### Additional Security Headers
- **X-Frame-Options: DENY** - Prevents clickjacking attacks
- **X-Content-Type-Options: nosniff** - Prevents MIME type sniffing
- **X-XSS-Protection** - Legacy XSS filter for older browsers

---

## 🧪 Testing Security Features

### Test Rate Limiting

**Using curl** (Windows PowerShell):
```powershell
# Test search endpoint - should fail after 30 requests
for ($i=1; $i -le 35; $i++) { 
    curl http://localhost:8000/api-proxy/naruto 
    Write-Host "Request $i"
}
```

**Expected Result**: 
- First 30 requests: Normal response (200)
- Requests 31-35: HTTP 429 (Too Many Requests)

### Test CSP Headers

**Using curl**:
```powershell
curl -I http://localhost:8000/
```

**Expected Headers**:
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com; ...
```

**Using Browser DevTools**:
1. Open browser Developer Tools (F12)
2. Navigate to **Console** tab
3. Look for CSP violation errors (there should be none)
4. Check **Network** tab → Click any request → **Headers** → Look for `Content-Security-Policy`

### Test HTTPS Redirect (Production)

**Requirements**: Deploy to production with `DEBUG=False`

```powershell
curl -I http://yourdomain.com
```

**Expected**: HTTP 301 redirect to `https://yourdomain.com`

---

## ⚙️ Development vs Production

### Development Mode (`DEBUG=True`)
- ✅ Rate limiting: **ENABLED**
- ✅ CSP headers: **ENABLED**
- ❌ HTTPS redirect: **DISABLED**
- ❌ HSTS headers: **DISABLED**
- ❌ Secure cookies: **DISABLED**

### Production Mode (`DEBUG=False`)
- ✅ Rate limiting: **ENABLED**
- ✅ CSP headers: **ENABLED**  
- ✅ HTTPS redirect: **ENABLED**
- ✅ HSTS headers: **ENABLED**
- ✅ Secure cookies: **ENABLED**

**Reason**: HTTPS-related features are disabled in development to allow testing on `http://localhost`.

---

## 🛠️ Troubleshooting

### Issue: Resources Not Loading (CSP Violations)

**Symptom**: Fonts, images, or scripts fail to load. Browser console shows CSP errors.

**Solution**: Add the resource's domain to the appropriate CSP directive in `settings.py`.

Example - adding a new CDN:
```python
CSP_SCRIPT_SRC = (
    "'self'",
    'https://cdnjs.cloudflare.com',
    'https://newcdn.example.com',  # Add here
)
```

### Issue: Rate Limit Too Restrictive

**Symptom**: Users report "429 Too Many Requests" errors during normal usage.

**Solution**: Increase rate limits in `app/views.py`:
```python
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # Was 30/m
```

### Issue: Development Server Shows HTTPS Errors

**Symptom**: Local development redirects to HTTPS incorrectly.

**Solution**: Ensure `DEBUG=True` in your `.env` file:
```env
DEBUG=True
```

### Issue: CSP Blocks Inline Scripts

**Symptom**: Inline `<script>` tags or `onclick` attributes don't work.

**Solution**: 
1. **Best Practice**: Move inline scripts to external `.js` files
2. **Alternative**: Use CSP nonces (advanced, not covered here)
3. **Last Resort**: Add `'unsafe-inline'` to `CSP_SCRIPT_SRC` (NOT recommended)

---

## 📋 Security Checklist for Production Deployment

Before deploying to production:

- [ ] Set `DEBUG=False` in `.env`
- [ ] Set strong `SECRET_KEY` (not the default)
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Ensure HTTPS is configured on hosting platform
- [ ] Test rate limiting with load testing tools
- [ ] Verify CSP headers using browser DevTools
- [ ] Check security headers at [securityheaders.com](https://securityheaders.com)
- [ ] Update dependencies regularly: `pip install --upgrade -r requirements.txt`
- [ ] Monitor rate limit violations in logs
- [ ] Set up error monitoring (Sentry recommended)

---

## 📚 Additional Resources

- **Django Security Docs**: https://docs.djangoproject.com/en/stable/topics/security/
- **django-ratelimit**: https://django-ratelimit.readthedocs.io/
- **django-csp**: https://django-csp.readthedocs.io/
- **OWASP CSP Guide**: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
- **Security Headers**: https://securityheaders.com

---

*Security configuration implemented: 2026-02-04*
