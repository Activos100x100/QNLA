using QNLA.Api.Models;
using Dapper;
using QNLA.Api.Data;

namespace QNLA.Api.Services;

public interface IParticipantService
{
    Task<ParticipantDto?> GetMyParticipantAsync(int torneoId, int empleadoId);
    Task<ParticipantDto?> UpdateMyParticipantAsync(int torneoId, int empleadoId, UpdateParticipantRequest request);
}

public sealed class ParticipantService(IConnectionFactory connectionFactory) : IParticipantService
{
    public async Task<ParticipantDto?> GetMyParticipantAsync(int torneoId, int empleadoId)
    {
        return await connectionFactory.WithConnection(async conn =>
        {
            const string sql = """
                SELECT
                    id,
                    torneo_id,
                    empleado_id,
                    nombre,
                    alias,
                    email,
                    activo,
                    es_admin
                FROM public.qnla_participantes
                WHERE torneo_id = @torneo_id
                  AND empleado_id = @empleado_id
                LIMIT 1;
                """;

            return await conn.QueryFirstOrDefaultAsync<ParticipantDto>(sql, new
            {
                torneo_id = torneoId,
                empleado_id = empleadoId
            });
        });
    }

    public async Task<ParticipantDto?> UpdateMyParticipantAsync(int torneoId, int empleadoId, UpdateParticipantRequest request)
    {
        if (request is null)
        {
            return null;
        }

        var nombre = string.IsNullOrWhiteSpace(request.Nombre) ? null : request.Nombre.Trim();
        var alias = string.IsNullOrWhiteSpace(request.Alias) ? null : request.Alias.Trim();

        return await connectionFactory.WithConnection(async conn =>
        {
            const string sql = """
                UPDATE public.qnla_participantes
                SET
                    nombre = COALESCE(@nombre, nombre),
                    alias = COALESCE(@alias, alias)
                WHERE torneo_id = @torneo_id
                  AND empleado_id = @empleado_id
                RETURNING
                    id,
                    torneo_id,
                    empleado_id,
                    nombre,
                    alias,
                    email,
                    activo,
                    es_admin;
                """;

            return await conn.QueryFirstOrDefaultAsync<ParticipantDto>(sql, new
            {
                torneo_id = torneoId,
                empleado_id = empleadoId,
                nombre,
                alias
            });
        });
    }
}