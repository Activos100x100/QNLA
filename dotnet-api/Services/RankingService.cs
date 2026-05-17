using Dapper;
using QNLA.Api.Data;
using QNLA.Api.Models;

namespace QNLA.Api.Services;

public interface IRankingService
{
    Task<RankingResponse> GetRankingAsync(int torneoId, int limit, int empleadoId);
    Task<IReadOnlyList<TorneoDto>> GetTorneosActivosAsync();
    Task<IReadOnlyList<PartidoDto>> GetPartidosAsync(int torneoId, bool soloPendientes);
    Task<int> CalcularPuntosPartidoAsync(int partidoId);
}

public sealed class RankingService(IConnectionFactory connectionFactory) : IRankingService
{
    private const int MaxRankingLimit = 500;
    private const string RankedCte = @"
        WITH ranked AS (
            SELECT
                ROW_NUMBER() OVER (ORDER BY puntos_totales DESC, aciertos_exactos DESC) AS posicion,
                torneo_id,
                participante_id,
                empleado_id,
                nombre_completo,
                alias,
                pronosticos_realizados,
                aciertos_exactos,
                aciertos_ganador,
                puntos_totales
            FROM qnla_v_ranking
            WHERE torneo_id = @torneo_id
        )";

    public async Task<RankingResponse> GetRankingAsync(int torneoId, int limit, int empleadoId)
    {
        var validatedLimit = Math.Clamp(limit, 1, MaxRankingLimit);

        return await connectionFactory.WithConnection(async conn =>
        {
            var sql = $"{RankedCte} SELECT * FROM ranked ORDER BY posicion LIMIT @limit;";

            var top = (await conn.QueryAsync<RankingRowDto>(sql, new { torneo_id = torneoId, limit = validatedLimit })).ToList();

            var currentSql = $"{RankedCte} SELECT * FROM ranked WHERE empleado_id = @empleado_id LIMIT 1;";

            var myPosition = await conn.QueryFirstOrDefaultAsync<RankingRowDto>(currentSql, new { torneo_id = torneoId, empleado_id = empleadoId });

            return new RankingResponse(top.AsReadOnly(), myPosition);
        });
    }

    public async Task<IReadOnlyList<TorneoDto>> GetTorneosActivosAsync()
    {
        return await connectionFactory.WithConnection(async conn =>
        {
            var rows = await conn.QueryAsync<TorneoDto>(@"
                SELECT id, nombre, anio, activo, cierre_inscripcion, fecha_inicio, fecha_fin
                FROM qnla_torneos
                WHERE activo = TRUE
                ORDER BY fecha_inicio DESC NULLS LAST, id DESC");

            return rows.ToList().AsReadOnly();
        });
    }

    public async Task<IReadOnlyList<PartidoDto>> GetPartidosAsync(int torneoId, bool soloPendientes)
    {
        return await connectionFactory.WithConnection(async conn =>
        {
            var rows = await conn.QueryAsync<PartidoDto>(@"
                SELECT p.id,
                       p.torneo_id,
                       p.fase_id,
                       p.grupo_id,
                       p.fecha_partido,
                       p.cierre_pronostico,
                       sl.nombre AS seleccion_local,
                       sv.nombre AS seleccion_visitante,
                       p.goles_local,
                       p.goles_visitante,
                       p.finalizado
                FROM qnla_partidos p
                LEFT JOIN qnla_selecciones sl ON sl.id = p.seleccion_local_id
                LEFT JOIN qnla_selecciones sv ON sv.id = p.seleccion_visitante_id
                WHERE p.torneo_id = @torneo_id
                  AND (@solo_pendientes = FALSE OR (p.finalizado = FALSE AND NOW() < p.cierre_pronostico))
                ORDER BY p.fecha_partido", new { torneo_id = torneoId, solo_pendientes = soloPendientes });

            return rows.ToList().AsReadOnly();
        });
    }

    public async Task<int> CalcularPuntosPartidoAsync(int partidoId)
    {
        return await connectionFactory.WithConnection(async conn =>
        {
            var updated = await conn.ExecuteScalarAsync<int>(
                "SELECT public.qnla_calcular_puntos_partido(@partido_id)",
                new { partido_id = partidoId });
            return updated;
        });
    }
}
