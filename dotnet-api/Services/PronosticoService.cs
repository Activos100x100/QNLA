using Dapper;
using QNLA.Api.Data;
using QNLA.Api.Models;

namespace QNLA.Api.Services;

public interface IPronosticoService
{
    Task<(int statusCode, object payload)> UpsertPronosticoAsync(int empleadoId, PronosticoUpsertRequest request);
    Task<(int statusCode, object payload)> UpdatePronosticoAsync(int empleadoId, int pronosticoId, PronosticoUpdateRequest request);
    Task<IReadOnlyList<PronosticoItemDto>> GetMisPronosticosAsync(int empleadoId, int torneoId);
    Task<(int statusCode, object payload)> DeletePronosticoAsync(int empleadoId, int pronosticoId);
}

public sealed class PronosticoService(IConnectionFactory connectionFactory) : IPronosticoService
{
    public async Task<(int statusCode, object payload)> UpsertPronosticoAsync(int empleadoId, PronosticoUpsertRequest request)
    {
        if (request.Goles_Local < 0 || request.Goles_Visitante < 0)
        {
            return (422, new { detail = "Los goles no pueden ser negativos." });
        }

        return await connectionFactory.WithConnection(async conn =>
        {
            var partido = await conn.QueryFirstOrDefaultAsync<(int Id, DateTime Cierre_Pronostico, bool Finalizado)>(
                "SELECT id, cierre_pronostico, finalizado FROM qnla_partidos WHERE id = @partido_id AND torneo_id = @torneo_id",
                new { partido_id = request.Partido_Id, torneo_id = request.Torneo_Id });

            if (partido == default)
            {
                return ((int)422, (object)new { detail = "Partido no existe para el torneo indicado." });
            }

            if (IsPronosticoClosed(partido.Cierre_Pronostico, partido.Finalizado))
            {
                return ((int)409, (object)new { detail = "Pronósticos cerrados para este partido" });
            }

            var participanteId = await conn.QueryFirstOrDefaultAsync<int?>(
                "SELECT id FROM qnla_participantes WHERE torneo_id = @torneo_id AND empleado_id = @empleado_id",
                new { torneo_id = request.Torneo_Id, empleado_id = empleadoId });

            if (!participanteId.HasValue)
            {
                var torneoInscripcionAbierta = await conn.QueryFirstOrDefaultAsync<bool>(@"
                    SELECT EXISTS(
                      SELECT 1
                      FROM qnla_torneos t
                      WHERE t.id = @torneo_id
                        AND t.activo = TRUE
                        AND (t.cierre_inscripcion IS NULL OR NOW() < t.cierre_inscripcion)
                    )", new { torneo_id = request.Torneo_Id });

                if (!torneoInscripcionAbierta)
                {
                    return ((int)422, (object)new { detail = "No estás inscrito y el torneo no admite nuevas inscripciones." });
                }

                participanteId = await conn.QuerySingleAsync<int>(@"
                    INSERT INTO qnla_participantes (torneo_id, empleado_id, activo)
                    VALUES (@torneo_id, @empleado_id, TRUE)
                    RETURNING id;", new { torneo_id = request.Torneo_Id, empleado_id = empleadoId });
            }

            var pronosticoId = await conn.QuerySingleAsync<int>(@"
                INSERT INTO qnla_pronosticos (participante_id, partido_id, goles_local, goles_visitante)
                VALUES (@participante_id, @partido_id, @goles_local, @goles_visitante)
                ON CONFLICT (participante_id, partido_id)
                DO UPDATE SET goles_local = EXCLUDED.goles_local,
                              goles_visitante = EXCLUDED.goles_visitante,
                              updated_at = NOW()
                RETURNING id;",
                new
                {
                    participante_id = participanteId.Value,
                    partido_id = request.Partido_Id,
                    goles_local = request.Goles_Local,
                    goles_visitante = request.Goles_Visitante
                });

            return ((int)200, (object)new { id = pronosticoId });
        });
    }

    public async Task<(int statusCode, object payload)> UpdatePronosticoAsync(int empleadoId, int pronosticoId, PronosticoUpdateRequest request)
    {
        if (request.Goles_Local < 0 || request.Goles_Visitante < 0)
        {
            return (422, new { detail = "Los goles no pueden ser negativos." });
        }

        return await connectionFactory.WithConnection(async conn =>
        {
            var row = await conn.QueryFirstOrDefaultAsync<(int Id, int Empleado_Id, DateTime Cierre_Pronostico, bool Finalizado)>(@"
                SELECT p.id, pa.empleado_id, m.cierre_pronostico, m.finalizado
                FROM qnla_pronosticos p
                JOIN qnla_participantes pa ON pa.id = p.participante_id
                JOIN qnla_partidos m ON m.id = p.partido_id
                WHERE p.id = @id", new { id = pronosticoId });

            if (row == default)
            {
                return ((int)404, (object)new { detail = "Pronóstico no encontrado." });
            }

            if (row.Empleado_Id != empleadoId)
            {
                return ((int)403, (object)new { detail = "No autorizado para editar este pronóstico." });
            }

            if (IsPronosticoClosed(row.Cierre_Pronostico, row.Finalizado))
            {
                return ((int)409, (object)new { detail = "Pronósticos cerrados para este partido" });
            }

            await conn.ExecuteAsync(@"
                UPDATE qnla_pronosticos
                SET goles_local = @goles_local,
                    goles_visitante = @goles_visitante,
                    updated_at = NOW()
                WHERE id = @id",
                new { id = pronosticoId, goles_local = request.Goles_Local, goles_visitante = request.Goles_Visitante });

            return ((int)200, (object)new { id = pronosticoId });
        });
    }

    public async Task<IReadOnlyList<PronosticoItemDto>> GetMisPronosticosAsync(int empleadoId, int torneoId)
    {
        return await connectionFactory.WithConnection(async conn =>
        {
            var rows = await conn.QueryAsync<PronosticoItemDto>(@"
                SELECT p.id,
                       p.partido_id,
                       m.fecha_partido,
                       m.cierre_pronostico,
                       sl.nombre AS seleccion_local,
                       sv.nombre AS seleccion_visitante,
                       p.goles_local,
                       p.goles_visitante,
                       p.puntos_obtenidos
                FROM qnla_pronosticos p
                JOIN qnla_participantes pa ON pa.id = p.participante_id
                JOIN qnla_partidos m ON m.id = p.partido_id
                LEFT JOIN qnla_selecciones sl ON sl.id = m.seleccion_local_id
                LEFT JOIN qnla_selecciones sv ON sv.id = m.seleccion_visitante_id
                WHERE pa.empleado_id = @empleado_id
                  AND pa.torneo_id = @torneo_id
                ORDER BY m.fecha_partido", new { empleado_id = empleadoId, torneo_id = torneoId });

            return rows.ToList().AsReadOnly();
        });
    }

    public async Task<(int statusCode, object payload)> DeletePronosticoAsync(int empleadoId, int pronosticoId)
    {
        return await connectionFactory.WithConnection(async conn =>
        {
            var row = await conn.QueryFirstOrDefaultAsync<(int Id, int Empleado_Id, DateTime Cierre_Pronostico, bool Finalizado)>(@"
                SELECT p.id, pa.empleado_id, m.cierre_pronostico, m.finalizado
                FROM qnla_pronosticos p
                JOIN qnla_participantes pa ON pa.id = p.participante_id
                JOIN qnla_partidos m ON m.id = p.partido_id
                WHERE p.id = @id", new { id = pronosticoId });

            if (row == default)
            {
                return ((int)404, (object)new { detail = "Pronóstico no encontrado." });
            }

            if (row.Empleado_Id != empleadoId)
            {
                return ((int)403, (object)new { detail = "No autorizado para eliminar este pronóstico." });
            }

            if (IsPronosticoClosed(row.Cierre_Pronostico, row.Finalizado))
            {
                return ((int)409, (object)new { detail = "Pronósticos cerrados para este partido" });
            }

            await conn.ExecuteAsync("DELETE FROM qnla_pronosticos WHERE id = @id", new { id = pronosticoId });
            return ((int)200, (object)new { id = pronosticoId, deleted = true });
        });
    }

    private static bool IsPronosticoClosed(DateTime cierrePronostico, bool finalizado)
        => finalizado || DateTime.UtcNow >= cierrePronostico.ToUniversalTime();
}
