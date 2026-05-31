using Microsoft.AspNetCore.Components.Authorization;
using System.Security.Claims;

namespace QLNA.Web.Services;

public class SessionTokenStore
{
    private readonly AuthenticationStateProvider _authProvider;
    private readonly IHttpContextAccessor _http;

    public SessionTokenStore(AuthenticationStateProvider authProvider, IHttpContextAccessor http)
    {
        _authProvider = authProvider;
        _http = http;
    }

    public async Task<string?> GetAccessTokenAsync()
    {
        // 1) Prefer AuthenticationStateProvider (works in interactive Blazor Server)
        var state = await _authProvider.GetAuthenticationStateAsync();
        var fromState = state.User?.FindFirst("access_token")?.Value;
        if (!string.IsNullOrWhiteSpace(fromState))
        {
            return fromState;
        }

        // 2) Fallback: HttpContext (only valid during prerender/SSR)
        return _http.HttpContext?.User?.FindFirst("access_token")?.Value;
    }

    public async Task<int?> GetUsuarioIdAsync()
    {
        var state = await _authProvider.GetAuthenticationStateAsync();
        var raw = state.User?.FindFirst(ClaimTypes.NameIdentifier)?.Value
                  ?? state.User?.FindFirst("usuario_id")?.Value;
        return int.TryParse(raw, out var id) ? id : null;
    }
}
