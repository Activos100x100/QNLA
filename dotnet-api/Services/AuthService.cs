using Dapper;
using QNLA.Api.Auth;
using QNLA.Api.Data;
using QNLA.Api.Models;

namespace QNLA.Api.Services;

public interface IAuthService
{
    Task<LoginResponse?> LoginAsync(LoginRequest request);
    Task<AccessTokenResponse?> RefreshAsync(string refreshToken);
    Task<UsuarioDto?> GetCurrentUserAsync(int empleadoId, string? dniNieFromToken);
}

public sealed class AuthService(
    IConnectionFactory connectionFactory,
    IPasswordHasher passwordHasher,
    IJwtService jwtService) : IAuthService
{
    public async Task<LoginResponse?> LoginAsync(LoginRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.Dni_Nie) || string.IsNullOrWhiteSpace(request.Password))
        {
            return null;
        }

        var empleadoColumns = await GetEmpleadoColumnsAsync();

        var nombreExpr = empleadoColumns.Contains("nombre") ? "e.nombre AS nombre" : "NULL::text AS nombre";
        var apellidosExpr = empleadoColumns.Contains("apellidos") ? "e.apellidos AS apellidos" : "NULL::text AS apellidos";
        var emailExpr = empleadoColumns.Contains("email") ? "e.email AS email" : "NULL::text AS email";

        var user = await connectionFactory.WithConnection(async conn =>
        {
            var sql = $@"
                SELECT ul.usuario_id, ul.empleado_id, ul.dni_nie, ul.password_hash, ul.password_salt, ul.activo,
                       {nombreExpr}, {apellidosExpr}, {emailExpr}
                FROM public.usuarios_login ul
                LEFT JOIN public.empleados e ON e.id = ul.empleado_id
                WHERE ul.dni_nie = @dni_nie AND ul.activo = TRUE
                LIMIT 1;";

            return await conn.QueryFirstOrDefaultAsync<UsuarioLoginRow>(sql, new { dni_nie = request.Dni_Nie });
        });

        if (user is null)
        {
            return null;
        }

        if (!passwordHasher.Verify(request.Password, user.Password_Hash, user.Password_Salt))
        {
            return null;
        }

        var payload = new TokenPayload
        {
            Empleado_Id = user.Empleado_Id,
            Dni_Nie = user.Dni_Nie,
            Nombre = user.Nombre
        };

        var (accessToken, accessExpiresIn) = jwtService.CreateAccessToken(payload);
        var (refreshToken, _) = jwtService.CreateRefreshToken(payload);

        return new LoginResponse(
            accessToken,
            refreshToken,
            accessExpiresIn,
            new UsuarioDto(user.Empleado_Id, user.Dni_Nie, user.Nombre, user.Apellidos, user.Email));
    }

    public Task<AccessTokenResponse?> RefreshAsync(string refreshToken)
    {
        if (string.IsNullOrWhiteSpace(refreshToken))
        {
            return Task.FromResult<AccessTokenResponse?>(null);
        }

        var principal = jwtService.ValidateRefreshToken(refreshToken);
        if (principal is null)
        {
            return Task.FromResult<AccessTokenResponse?>(null);
        }

        var empleadoIdClaim = principal.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value
                              ?? principal.FindFirst("sub")?.Value;

        if (!int.TryParse(empleadoIdClaim, out var empleadoId))
        {
            return Task.FromResult<AccessTokenResponse?>(null);
        }

        var payload = new TokenPayload
        {
            Empleado_Id = empleadoId,
            Dni_Nie = principal.FindFirst("dni_nie")?.Value ?? string.Empty,
            Nombre = principal.FindFirst("nombre")?.Value
        };

        var (accessToken, expiresIn) = jwtService.CreateAccessToken(payload);
        return Task.FromResult<AccessTokenResponse?>(new AccessTokenResponse(accessToken, expiresIn));
    }

    public async Task<UsuarioDto?> GetCurrentUserAsync(int empleadoId, string? dniNieFromToken)
    {
        var empleadoColumns = await GetEmpleadoColumnsAsync();
        var nombreExpr = empleadoColumns.Contains("nombre") ? "e.nombre AS nombre" : "NULL::text AS nombre";
        var apellidosExpr = empleadoColumns.Contains("apellidos") ? "e.apellidos AS apellidos" : "NULL::text AS apellidos";
        var emailExpr = empleadoColumns.Contains("email") ? "e.email AS email" : "NULL::text AS email";

        return await connectionFactory.WithConnection(async conn =>
        {
            var sql = $@"
                SELECT ul.empleado_id, ul.dni_nie, {nombreExpr}, {apellidosExpr}, {emailExpr}
                FROM public.usuarios_login ul
                LEFT JOIN public.empleados e ON e.id = ul.empleado_id
                WHERE ul.empleado_id = @empleado_id
                LIMIT 1;";

            var row = await conn.QueryFirstOrDefaultAsync<UsuarioDto>(sql, new { empleado_id = empleadoId });
            if (row is not null)
            {
                return row;
            }

            if (string.IsNullOrWhiteSpace(dniNieFromToken))
            {
                return null;
            }

            return new UsuarioDto(empleadoId, dniNieFromToken, null, null, null);
        });
    }

    private Task<HashSet<string>> GetEmpleadoColumnsAsync()
    {
        return connectionFactory.WithConnection(async conn =>
        {
            var sql = @"SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'empleados'
                          AND column_name IN ('nombre','apellidos','email')";
            var cols = await conn.QueryAsync<string>(sql);
            return cols.Select(x => x.ToLowerInvariant()).ToHashSet();
        });
    }
}
