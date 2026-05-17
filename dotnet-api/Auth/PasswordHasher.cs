using System.Security.Cryptography;
using Microsoft.Extensions.Options;
using QNLA.Api.Models;

namespace QNLA.Api.Auth;

public interface IPasswordHasher
{
    bool Verify(string plainPassword, string storedHash, string storedSalt);
}

public sealed class PasswordHasher(
    IOptions<PasswordHashingOptions> options,
    ILogger<PasswordHasher> logger) : IPasswordHasher
{
    private readonly PasswordHashingOptions _options = options.Value;

    public bool Verify(string plainPassword, string storedHash, string storedSalt)
    {
        if (string.IsNullOrWhiteSpace(plainPassword) || string.IsNullOrWhiteSpace(storedHash) || string.IsNullOrWhiteSpace(storedSalt))
        {
            return false;
        }

        var encoding = _options.Encoding?.Trim() ?? "Base64";

        if (encoding.Equals("Base64", StringComparison.OrdinalIgnoreCase))
        {
            if (TryVerifyWithEncoding(plainPassword, storedHash, storedSalt, "Base64", out var verified) && verified)
            {
                return true;
            }

            if (TryVerifyWithEncoding(plainPassword, storedHash, storedSalt, "Hex", out verified) && verified)
            {
                logger.LogWarning("Password hash verified using Hex fallback encoding at {UtcNow}.", DateTime.UtcNow);
                return true;
            }

            return false;
        }

        return TryVerifyWithEncoding(plainPassword, storedHash, storedSalt, encoding, out var result) && result;
    }

    private bool TryVerifyWithEncoding(string plainPassword, string storedHash, string storedSalt, string encoding, out bool verified)
    {
        verified = false;
        if (!TryDecode(storedHash, encoding, out var expectedHash) || !TryDecode(storedSalt, encoding, out var saltBytes))
        {
            return false;
        }

        var computedHash = ComputeHash(plainPassword, saltBytes);
        verified = CryptographicOperations.FixedTimeEquals(expectedHash, computedHash);
        return true;
    }

    private byte[] ComputeHash(string plainPassword, byte[] salt)
    {
        if (!_options.Algorithm.Equals("PBKDF2-SHA256", StringComparison.OrdinalIgnoreCase))
        {
            throw new NotSupportedException($"Password algorithm '{_options.Algorithm}' is not supported.");
        }

        return Rfc2898DeriveBytes.Pbkdf2(
            plainPassword,
            salt,
            _options.Iterations,
            HashAlgorithmName.SHA256,
            _options.HashSizeBytes);
    }

    private static bool TryDecode(string value, string encoding, out byte[] bytes)
    {
        bytes = Array.Empty<byte>();

        try
        {
            if (encoding.Equals("Base64", StringComparison.OrdinalIgnoreCase))
            {
                bytes = Convert.FromBase64String(value);
                return true;
            }

            if (encoding.Equals("Hex", StringComparison.OrdinalIgnoreCase))
            {
                bytes = Convert.FromHexString(value);
                return true;
            }

            return false;
        }
        catch (FormatException)
        {
            return false;
        }
    }
}
