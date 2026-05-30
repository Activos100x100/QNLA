using System.Security.Claims;
using Microsoft.AspNetCore.Components.Authorization;
using QLNA.Web.Models;

namespace QLNA.Web.Services;

public class AuthStateProvider : AuthenticationStateProvider
{
    private readonly SessionTokenStore _sessionTokenStore;

    public AuthStateProvider(SessionTokenStore sessionTokenStore)
    {
        _sessionTokenStore = sessionTokenStore;
    }

    public override Task<AuthenticationState> GetAuthenticationStateAsync()
    {
        _sessionTokenStore.EnsureHydratedFromCookie();

        if (string.IsNullOrWhiteSpace(_sessionTokenStore.AccessToken))
        {
            return Task.FromResult(new AuthenticationState(new ClaimsPrincipal(new ClaimsIdentity())));
        }

        var user = _sessionTokenStore.UsuarioActual;
        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, user?.usuario_id?.ToString() ?? user?.usuario?.empleado_id?.ToString() ?? "0"),
            new(ClaimTypes.Name, user?.nombre ?? user?.usuario?.nombre ?? "Usuario")
        };

        var identity = new ClaimsIdentity(claims, "SessionToken");
        return Task.FromResult(new AuthenticationState(new ClaimsPrincipal(identity)));
    }

    public Task NotifyLoginAsync()
    {
        NotifyAuthenticationStateChanged(GetAuthenticationStateAsync());
        return Task.CompletedTask;
    }

    public Task SignOutAsync()
    {
        _sessionTokenStore.Clear();
        NotifyAuthenticationStateChanged(GetAuthenticationStateAsync());
        return Task.CompletedTask;
    }

    public void UpdateSession(string accessToken, LoginResponse response)
    {
        _sessionTokenStore.SetSession(accessToken, response);
        NotifyAuthenticationStateChanged(GetAuthenticationStateAsync());
    }
}
