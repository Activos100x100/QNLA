namespace QNLA.Api.Models;

public sealed class UsuarioLoginRow
{
    public int Usuario_Id { get; init; }
    public int Empleado_Id { get; init; }
    public string Dni_Nie { get; init; } = string.Empty;
    public string Password_Hash { get; init; } = string.Empty;
    public string Password_Salt { get; init; } = string.Empty;
    public bool Activo { get; init; }
    public string? Nombre { get; init; }
    public string? Apellidos { get; init; }
    public string? Email { get; init; }
}

public sealed class TokenPayload
{
    public int Empleado_Id { get; init; }
    public string Dni_Nie { get; init; } = string.Empty;
    public string? Nombre { get; init; }
}

public sealed class JwtOptions
{
    public string Secret { get; init; } = string.Empty;
    public string Issuer { get; init; } = "QNLA.Api";
    public string Audience { get; init; } = "QNLA.Mobile";
    public int AccessTokenMinutes { get; init; } = 60;
    public int RefreshTokenDays { get; init; } = 30;
}

public sealed class PasswordHashingOptions
{
    public string Algorithm { get; init; } = "PBKDF2-SHA256";
    public int Iterations { get; init; } = 100000;
    public int HashSizeBytes { get; init; } = 32;
    public string Encoding { get; init; } = "Base64";
}
