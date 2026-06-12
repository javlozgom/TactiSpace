from __future__ import annotations

import json
import os
import time

import mysql.connector
import requests


COMPETITION_ID = 55
SEASON_ID = 282
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
SLEEP = 0.12
TIMEOUT = 30
RETRIES = 4


def get_db_config() -> dict[str, str]:
    """Build the MySQL connection config from environment variables."""
    config = {
        "host": os.getenv("DB_HOST", ""),
        "user": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", ""),
    }
    missing = [key for key, value in config.items() if not value]
    if missing:
        missing_vars = ", ".join(missing)
        raise RuntimeError(
            "Faltan variables de entorno para la base de datos: "
            f"{missing_vars}. Define DB_HOST, DB_USER, DB_PASSWORD y DB_NAME."
        )
    return config


def get_json(url: str):
    """Download JSON with basic retry handling."""
    last = None
    for i in range(1, RETRIES + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 404:
                return None
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover
            last = exc
            time.sleep(0.5 * i)
    raise RuntimeError(f"Error descargando {url}. Ultimo error: {last}")


def jdump(obj):
    """Serialize nested values to JSON when present."""
    return json.dumps(obj, ensure_ascii=False) if obj is not None else None


def main():
    """Import StatsBomb open data into MySQL."""
    conn = mysql.connector.connect(**get_db_config())
    cursor = conn.cursor()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("DROP TABLE IF EXISTS lineups_positions;")
    cursor.execute("DROP TABLE IF EXISTS lineups_players;")
    cursor.execute("DROP TABLE IF EXISTS lineups_teams;")
    cursor.execute("DROP TABLE IF EXISTS three_sixty;")
    cursor.execute("DROP TABLE IF EXISTS lineups;")
    cursor.execute("DROP TABLE IF EXISTS events;")
    cursor.execute("DROP TABLE IF EXISTS matches;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    print("Tablas eliminadas completamente")

    cursor.execute(
        """
        CREATE TABLE matches (
            match_id BIGINT PRIMARY KEY,
            match_date DATE,
            kick_off VARCHAR(50),
            competition JSON,
            season JSON,
            home_team JSON,
            away_team JSON,
            home_score INT,
            away_score INT,
            match_status VARCHAR(50),
            match_status_360 VARCHAR(50),
            last_updated VARCHAR(100),
            last_updated_360 VARCHAR(100),
            metadata JSON,
            match_week INT,
            competition_stage JSON,
            stadium JSON,
            referee JSON
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE events (
            event_id VARCHAR(64) PRIMARY KEY,
            match_id BIGINT,
            index_event INT,
            period INT,
            timestamp VARCHAR(50),
            minute INT,
            second INT,
            type_name VARCHAR(255),
            possession_team VARCHAR(255),
            team_name VARCHAR(255),
            player_name VARCHAR(255),
            position_name VARCHAR(255),
            location_x FLOAT,
            location_y FLOAT,
            FOREIGN KEY (match_id) REFERENCES matches(match_id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE lineups (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            match_id BIGINT,
            team_id INT,
            team_name VARCHAR(255),
            player_id INT,
            player_name VARCHAR(255),
            player_nickname VARCHAR(255),
            jersey_number INT,
            country_id INT,
            country_name VARCHAR(255),
            position_id INT,
            position_name VARCHAR(255),
            from_time VARCHAR(20),
            to_time VARCHAR(20),
            from_period INT,
            to_period INT,
            start_reason VARCHAR(255),
            end_reason VARCHAR(255),
            FOREIGN KEY (match_id) REFERENCES matches(match_id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE lineups_teams (
            lineup_team_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            match_id BIGINT,
            team_id INT,
            team_name VARCHAR(255),
            UNIQUE KEY uniq_team (match_id, team_id),
            FOREIGN KEY (match_id) REFERENCES matches(match_id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE lineups_players (
            lineup_player_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            lineup_team_id BIGINT,
            player_id INT,
            player_name VARCHAR(255),
            jersey_number INT,
            player_nickname VARCHAR(255),
            country_id INT,
            country_name VARCHAR(255),
            UNIQUE KEY uniq_player (lineup_team_id, player_id),
            FOREIGN KEY (lineup_team_id) REFERENCES lineups_teams(lineup_team_id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE lineups_positions (
            lineup_position_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            lineup_player_id BIGINT,
            position_id INT,
            position_name VARCHAR(255),
            from_time VARCHAR(20),
            to_time VARCHAR(20),
            from_period INT,
            to_period INT,
            start_reason VARCHAR(255),
            end_reason VARCHAR(255),
            FOREIGN KEY (lineup_player_id) REFERENCES lineups_players(lineup_player_id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE three_sixty (
            event_uuid VARCHAR(50) PRIMARY KEY,
            visible_area JSON,
            freeze_frame JSON,
            match_id BIGINT,
            FOREIGN KEY (match_id) REFERENCES matches(match_id)
        );
        """
    )

    cursor.execute("CREATE INDEX idx_events_match ON events(match_id);")
    cursor.execute("CREATE INDEX idx_lineups_match ON lineups(match_id);")
    cursor.execute("CREATE INDEX idx_three_match ON three_sixty(match_id);")
    cursor.execute("CREATE INDEX idx_three_event ON three_sixty(event_uuid);")
    conn.commit()
    print("Tablas creadas (V7 + lineups V2 + events)")

    matches_url = f"{BASE_URL}/matches/{COMPETITION_ID}/{SEASON_ID}.json"
    matches = get_json(matches_url)
    if not matches:
        raise RuntimeError("No se pudieron descargar matches. Revisa COMPETITION_ID/SEASON_ID.")

    insert_matches_sql = """
    INSERT INTO matches (
        match_id, match_date, kick_off,
        competition, season, home_team, away_team,
        home_score, away_score,
        match_status, match_status_360,
        last_updated, last_updated_360,
        metadata, match_week,
        competition_stage, stadium, referee
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    for match in matches:
        cursor.execute(
            insert_matches_sql,
            (
                match["match_id"],
                match.get("match_date"),
                match.get("kick_off"),
                jdump(match.get("competition")),
                jdump(match.get("season")),
                jdump(match.get("home_team")),
                jdump(match.get("away_team")),
                match.get("home_score"),
                match.get("away_score"),
                match.get("match_status"),
                match.get("match_status_360"),
                match.get("last_updated"),
                match.get("last_updated_360"),
                jdump(match.get("metadata")),
                match.get("match_week"),
                jdump(match.get("competition_stage")),
                jdump(match.get("stadium")),
                jdump(match.get("referee")),
            ),
        )
    conn.commit()
    print(f"Insertados {len(matches)} partidos")

    insert_events_sql = """
    INSERT IGNORE INTO events (
        event_id, match_id, index_event, period, timestamp,
        minute, second, type_name, possession_team,
        team_name, player_name, position_name,
        location_x, location_y
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    insert_lineups_flat_sql = """
    INSERT INTO lineups (
        match_id, team_id, team_name,
        player_id, player_name, player_nickname, jersey_number,
        country_id, country_name,
        position_id, position_name,
        from_time, to_time, from_period, to_period,
        start_reason, end_reason
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    insert_team_sql = """
    INSERT INTO lineups_teams (match_id, team_id, team_name)
    VALUES (%s,%s,%s)
    ON DUPLICATE KEY UPDATE team_name=VALUES(team_name)
    """

    select_team_id_sql = """
    SELECT lineup_team_id FROM lineups_teams WHERE match_id=%s AND team_id=%s
    """

    insert_player_sql = """
    INSERT INTO lineups_players (
        lineup_team_id, player_id, player_name, jersey_number,
        player_nickname, country_id, country_name
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        player_name=VALUES(player_name),
        jersey_number=VALUES(jersey_number),
        player_nickname=VALUES(player_nickname),
        country_id=VALUES(country_id),
        country_name=VALUES(country_name)
    """

    select_player_id_sql = """
    SELECT lineup_player_id FROM lineups_players WHERE lineup_team_id=%s AND player_id=%s
    """

    insert_pos_sql = """
    INSERT INTO lineups_positions (
        lineup_player_id, position_id, position_name,
        from_time, to_time, from_period, to_period,
        start_reason, end_reason
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    insert_three_sql = """
    INSERT INTO three_sixty (event_uuid, visible_area, freeze_frame, match_id)
    VALUES (%s,%s,%s,%s)
    """

    for idx, match in enumerate(matches, start=1):
        match_id = match["match_id"]
        print(f"\n[{idx}/{len(matches)}] match_id={match_id}")

        try:
            ev_url = f"{BASE_URL}/events/{match_id}.json"
            ev_data = get_json(ev_url)
            if ev_data:
                for event in ev_data:
                    loc = event.get("location", [None, None])
                    cursor.execute(
                        insert_events_sql,
                        (
                            event.get("id"),
                            match_id,
                            event.get("index"),
                            event.get("period"),
                            event.get("timestamp"),
                            event.get("minute"),
                            event.get("second"),
                            event.get("type", {}).get("name") if event.get("type") else None,
                            event.get("possession_team", {}).get("name")
                            if event.get("possession_team")
                            else None,
                            event.get("team", {}).get("name") if event.get("team") else None,
                            event.get("player", {}).get("name") if event.get("player") else None,
                            event.get("position", {}).get("name") if event.get("position") else None,
                            loc[0],
                            loc[1],
                        ),
                    )
                conn.commit()
                print("  events")
            else:
                print("  events (no data / 404)")
        except Exception as exc:
            print(f"  events error: {exc}")

        time.sleep(SLEEP)

        try:
            lu_url = f"{BASE_URL}/lineups/{match_id}.json"
            lu_data = get_json(lu_url)
            if not lu_data:
                print("  lineups (no data / 404)")
                continue

            for team in lu_data:
                team_id = team.get("team_id")
                team_name = team.get("team_name")

                cursor.execute(insert_team_sql, (match_id, team_id, team_name))
                cursor.execute(select_team_id_sql, (match_id, team_id))
                lineup_team_id = cursor.fetchone()[0]

                for player in team.get("lineup", []):
                    player_id = player.get("player_id")
                    player_name = player.get("player_name")
                    jersey = player.get("jersey_number")
                    nickname = player.get("player_nickname")

                    country = player.get("country") or {}
                    country_id = country.get("id")
                    country_name = country.get("name")

                    cursor.execute(
                        insert_player_sql,
                        (
                            lineup_team_id,
                            player_id,
                            player_name,
                            jersey,
                            nickname,
                            country_id,
                            country_name,
                        ),
                    )
                    cursor.execute(select_player_id_sql, (lineup_team_id, player_id))
                    lineup_player_id = cursor.fetchone()[0]

                    positions = player.get("positions", [])
                    if not positions:
                        cursor.execute(
                            insert_lineups_flat_sql,
                            (
                                match_id,
                                team_id,
                                team_name,
                                player_id,
                                player_name,
                                nickname,
                                jersey,
                                country_id,
                                country_name,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                            ),
                        )
                        continue

                    for pos in positions:
                        pos_id = pos.get("position_id")
                        pos_name = pos.get("position")
                        from_t = pos.get("from")
                        to_t = pos.get("to")
                        from_p = pos.get("from_period")
                        to_p = pos.get("to_period")
                        start_r = pos.get("start_reason")
                        end_r = pos.get("end_reason")

                        cursor.execute(
                            insert_lineups_flat_sql,
                            (
                                match_id,
                                team_id,
                                team_name,
                                player_id,
                                player_name,
                                nickname,
                                jersey,
                                country_id,
                                country_name,
                                pos_id,
                                pos_name,
                                from_t,
                                to_t,
                                from_p,
                                to_p,
                                start_r,
                                end_r,
                            ),
                        )

                        cursor.execute(
                            insert_pos_sql,
                            (
                                lineup_player_id,
                                pos_id,
                                pos_name,
                                from_t,
                                to_t,
                                from_p,
                                to_p,
                                start_r,
                                end_r,
                            ),
                        )

            conn.commit()
            print("  lineups (plano + normalizado)")
        except Exception as exc:
            print(f"  lineups error: {exc}")

        time.sleep(SLEEP)

        try:
            ts_url = f"{BASE_URL}/three-sixty/{match_id}.json"
            ts_data = get_json(ts_url)
            if not ts_data:
                print("  three-sixty (no data / 404)")
                continue

            for item in ts_data:
                try:
                    cursor.execute(
                        insert_three_sql,
                        (
                            item.get("event_uuid"),
                            jdump(item.get("visible_area")),
                            jdump(item.get("freeze_frame")),
                            match_id,
                        ),
                    )
                except mysql.connector.IntegrityError:
                    pass

            conn.commit()
            print("  three-sixty")
        except Exception as exc:
            print(f"  three-sixty error: {exc}")

        time.sleep(SLEEP)

    cursor.close()
    conn.close()
    print("\nImportacion completada (V7 + lineups V2 + events)")


if __name__ == "__main__":
    main()
