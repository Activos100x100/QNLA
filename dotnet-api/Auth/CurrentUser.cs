using System.Security.Claims;

namespace QNLA.Api.Auth;

public interface ICurrentUser
{
    int? EmpleadoId { get; }
    string? DniNie { get; }
    string? Nombre { get; }
}

public sealed class CurrentUser(IHttpContextAccessor httpContextAccessor) : ICurrentUser
{
    private ClaimsPrincipal? User => httpContextAccessor.HttpContext?.User;

    public int? EmpleadoId => int.TryParse(User?.FindFirstValue(ClaimTypes.NameIdentifier), out var id) ? id : null;
    public string? DniNie => User?.FindFirstValue("dni_nie");
    public string? Nombre => User?.FindFirstValue("nombre");
}
