using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using QNLA.Api.Models;

namespace QNLA.Api.Auth;

public interface IJwtService
{
    (string token, int expiresInSeconds) CreateAccessToken(TokenPayload payload);
    (string token, int expiresInSeconds) CreateRefreshToken(TokenPayload payload);
    ClaimsPrincipal? ValidateRefreshToken(string refreshToken);
}

public sealed class JwtService(IOptions<JwtOptions> options) : IJwtService
{
    private readonly JwtOptions _options = options.Value;

    public (string token, int expiresInSeconds) CreateAccessToken(TokenPayload payload)
    {
        var expiresInSeconds = _options.AccessTokenMinutes * 60;
        var expiresAt = DateTime.UtcNow.AddMinutes(_options.AccessTokenMinutes);

        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, payload.Empleado_Id.ToString()),
            new(JwtRegisteredClaimNames.Sub, payload.Empleado_Id.ToString()),
            new("dni_nie", payload.Dni_Nie),
            new("nombre", payload.Nombre ?? string.Empty),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString())
        };

        var token = BuildToken(claims, expiresAt);
        return (token, expiresInSeconds);
    }

    public (string token, int expiresInSeconds) CreateRefreshToken(TokenPayload payload)
    {
        var expiresInSeconds = _options.RefreshTokenDays * 24 * 60 * 60;
        var expiresAt = DateTime.UtcNow.AddDays(_options.RefreshTokenDays);

        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, payload.Empleado_Id.ToString()),
            new(JwtRegisteredClaimNames.Sub, payload.Empleado_Id.ToString()),
            new("dni_nie", payload.Dni_Nie),
            new("nombre", payload.Nombre ?? string.Empty),
            new("token_type", "refresh"),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString())
        };

        var token = BuildToken(claims, expiresAt);
        return (token, expiresInSeconds);
    }

    public ClaimsPrincipal? ValidateRefreshToken(string refreshToken)
    {
        var tokenHandler = new JwtSecurityTokenHandler();

        try
        {
            var principal = tokenHandler.ValidateToken(refreshToken, new TokenValidationParameters
            {
                ValidateIssuer = true,
                ValidateAudience = true,
                ValidateIssuerSigningKey = true,
                ValidateLifetime = true,
                ValidIssuer = _options.Issuer,
                ValidAudience = _options.Audience,
                IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_options.Secret)),
                ClockSkew = TimeSpan.Zero
            }, out _);

            var isRefresh = principal.FindFirstValue("token_type") == "refresh";
            return isRefresh ? principal : null;
        }
        catch
        {
            return null;
        }
    }

    private string BuildToken(IEnumerable<Claim> claims, DateTime expiresAt)
    {
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_options.Secret));
        var credentials = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _options.Issuer,
            audience: _options.Audience,
            claims: claims,
            expires: expiresAt,
            signingCredentials: credentials);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}
