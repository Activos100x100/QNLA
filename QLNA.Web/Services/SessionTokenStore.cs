using System.Text.Json;
using Microsoft.AspNetCore.DataProtection;
using QLNA.Web.Models;

namespace QLNA.Web.Services;

public class SessionTokenStore
{
    private const string CookieName = "qlna_session";
    private readonly IHttpContextAccessor _httpContextAccessor;
    private readonly IDataProtector _protector;
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNameCaseInsensitive = true };
    private bool _hydrated;

    public string? AccessToken { get; private set; }
    public LoginResponse? UsuarioActual { get; private set; }

    public SessionTokenStore(IHttpContextAccessor httpContextAccessor, IDataProtectionProvider dataProtectionProvider)
    {
        _httpContextAccessor = httpContextAccessor;
        _protector = dataProtectionProvider.CreateProtector("QLNA.Web.SessionTokenStore.v1");
    }

    public void EnsureHydratedFromCookie()
    {
        if (_hydrated)
        {
            return;
        }

        _hydrated = true;
        try
        {
            var raw = _httpContextAccessor.HttpContext?.Request.Cookies[CookieName];
            if (string.IsNullOrWhiteSpace(raw))
            {
                return;
            }

            var json = _protector.Unprotect(raw);
            var payload = JsonSerializer.Deserialize<SessionPayload>(json, _jsonOptions);
            if (payload is null)
            {
                return;
            }

            AccessToken = payload.access_token;
            UsuarioActual = payload.usuario;
        }
        catch
        {
            AccessToken = null;
            UsuarioActual = null;
        }
    }

    public void SetSession(string? accessToken, LoginResponse? usuario)
    {
        AccessToken = accessToken;
        UsuarioActual = usuario;
        PersistCookie();
    }

    public void Clear()
    {
        AccessToken = null;
        UsuarioActual = null;

        try
        {
            _httpContextAccessor.HttpContext?.Response.Cookies.Delete(CookieName);
        }
        catch
        {
            // no-op
        }
    }

    private void PersistCookie()
    {
        try
        {
            var context = _httpContextAccessor.HttpContext;
            if (context is null || context.Response.HasStarted)
            {
                return;
            }

            var payload = new SessionPayload
            {
                access_token = AccessToken,
                usuario = UsuarioActual
            };

            var json = JsonSerializer.Serialize(payload, _jsonOptions);
            var value = _protector.Protect(json);
            context.Response.Cookies.Append(CookieName, value, new CookieOptions
            {
                HttpOnly = true,
                Secure = context.Request.IsHttps,
                SameSite = SameSiteMode.Lax,
                Expires = DateTimeOffset.UtcNow.AddHours(12)
            });
        }
        catch
        {
            // no-op
        }
    }

    private sealed class SessionPayload
    {
        public string? access_token { get; set; }
        public LoginResponse? usuario { get; set; }
    }
}
