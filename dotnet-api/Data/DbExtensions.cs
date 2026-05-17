using System.Data;

namespace QNLA.Api.Data;

public static class DbExtensions
{
    public static async Task<T> WithConnection<T>(this IConnectionFactory factory, Func<IDbConnection, Task<T>> action)
    {
        using var connection = factory.CreateConnection();
        return await action(connection);
    }

    public static async Task WithConnection(this IConnectionFactory factory, Func<IDbConnection, Task> action)
    {
        using var connection = factory.CreateConnection();
        await action(connection);
    }
}
