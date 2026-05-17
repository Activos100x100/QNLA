using System.Data;
using Microsoft.AspNetCore.WebUtilities;
using Npgsql;

namespace QNLA.Api.Data;

public interface IConnectionFactory
{
    IDbConnection CreateConnection();
}

public sealed class ConnectionFactory(IConfiguration configuration) : IConnectionFactory
{
    public IDbConnection CreateConnection()
    {
        var connectionString = BuildConnectionString(configuration);
        return new NpgsqlConnection(connectionString);
    }

    internal static string BuildConnectionString(IConfiguration configuration)
    {
        var databaseUrl = Environment.GetEnvironmentVariable("DATABASE_URL")
                          ?? configuration["DATABASE_URL"];

        if (!string.IsNullOrWhiteSpace(databaseUrl))
        {
            return ConvertDatabaseUrl(databaseUrl, configuration);
        }

        var dbHost = Environment.GetEnvironmentVariable("DB_HOST") ?? configuration["DB_HOST"];
        var dbName = Environment.GetEnvironmentVariable("DB_NAME") ?? configuration["DB_NAME"];
        var dbUser = Environment.GetEnvironmentVariable("DB_USER") ?? configuration["DB_USER"];
        var dbPassword = Environment.GetEnvironmentVariable("DB_PASSWORD") ?? configuration["DB_PASSWORD"];
        var dbPort = Environment.GetEnvironmentVariable("DB_PORT") ?? configuration["DB_PORT"] ?? "5432";
        var dbSslMode = Environment.GetEnvironmentVariable("DB_SSLMODE") ?? configuration["DB_SSLMODE"] ?? "require";

        if (string.IsNullOrWhiteSpace(dbHost) || string.IsNullOrWhiteSpace(dbName) || string.IsNullOrWhiteSpace(dbUser) || string.IsNullOrWhiteSpace(dbPassword))
        {
            throw new InvalidOperationException("Database configuration missing. Define DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD.");
        }

        var builder = new NpgsqlConnectionStringBuilder
        {
            Host = dbHost,
            Database = dbName,
            Username = dbUser,
            Password = dbPassword,
            Port = int.TryParse(dbPort, out var parsedPort) ? parsedPort : 5432,
            Pooling = true
        };

        if (!dbHost.StartsWith("/cloudsql/", StringComparison.OrdinalIgnoreCase))
        {
            builder.SslMode = ParseSslMode(dbSslMode);
        }

        return builder.ConnectionString;
    }

    private static string ConvertDatabaseUrl(string databaseUrl, IConfiguration configuration)
    {
        var postgresqlUrl = databaseUrl.StartsWith("postgres://", StringComparison.OrdinalIgnoreCase)
            ? "postgresql://" + databaseUrl["postgres://".Length..]
            : databaseUrl;
        var uri = new Uri(postgresqlUrl);

        var query = QueryHelpers.ParseQuery(uri.Query);
        var hostFromQuery = query.TryGetValue("host", out var hostValue) ? hostValue.ToString() : null;
        var sslModeValue = query.TryGetValue("sslmode", out var querySslMode) ? querySslMode.ToString() : null;

        var host = !string.IsNullOrWhiteSpace(hostFromQuery)
            ? Uri.UnescapeDataString(hostFromQuery)
            : uri.Host;
        var credentials = uri.UserInfo.Split(':', 2);

        var builder = new NpgsqlConnectionStringBuilder
        {
            Host = host,
            Port = uri.IsDefaultPort ? 5432 : uri.Port,
            Database = uri.AbsolutePath.Trim('/'),
            Username = Uri.UnescapeDataString(credentials[0]),
            Password = credentials.Length > 1
                ? Uri.UnescapeDataString(credentials[1])
                : string.Empty,
            Pooling = true
        };

        if (!host.StartsWith("/cloudsql/", StringComparison.OrdinalIgnoreCase))
        {
            var envSsl = Environment.GetEnvironmentVariable("DB_SSLMODE") ?? configuration["DB_SSLMODE"];
            var selectedSsl = !string.IsNullOrWhiteSpace(envSsl)
                ? envSsl
                : (!string.IsNullOrWhiteSpace(sslModeValue) ? sslModeValue : "require");
            builder.SslMode = ParseSslMode(selectedSsl);
        }

        return builder.ConnectionString;
    }

    private static SslMode ParseSslMode(string? sslMode)
    {
        return sslMode?.Trim().ToLowerInvariant() switch
        {
            "disable" => SslMode.Disable,
            "allow" => SslMode.Allow,
            "prefer" => SslMode.Prefer,
            "require" => SslMode.Require,
            "verify-ca" => SslMode.VerifyCA,
            "verify-full" => SslMode.VerifyFull,
            _ => SslMode.Require
        };
    }
}
