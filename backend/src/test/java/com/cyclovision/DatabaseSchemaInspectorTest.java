package com.cyclovision;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;
import java.util.Map;

@SpringBootTest
public class DatabaseSchemaInspectorTest {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void inspectDatabaseSchema() {
        System.out.println("================================================================================");
        System.out.println("                       LIVE SUPABASE SCHEMA INTROSPECTION                       ");
        System.out.println("================================================================================");

        // 1. Version
        String pgVersion = jdbcTemplate.queryForObject("SELECT version()", String.class);
        System.out.println("\n--- [1] POSTGRESQL VERSION ---");
        System.out.println(pgVersion);

        // 2. PostGIS Extension
        System.out.println("\n--- [2] EXTENSIONS & POSTGIS STATUS ---");
        List<Map<String, Object>> extensions = jdbcTemplate.queryForList(
                "SELECT extname, extversion, extrelocatable FROM pg_extension ORDER BY extname"
        );
        for (Map<String, Object> ext : extensions) {
            System.out.printf("Installed Extension: %-25s | Version: %-15s\n", ext.get("extname"), ext.get("extversion"));
        }

        List<Map<String, Object>> availableExt = jdbcTemplate.queryForList(
                "SELECT name, default_version, comment FROM pg_available_extensions WHERE name LIKE 'postgis%' ORDER BY name"
        );
        for (Map<String, Object> ext : availableExt) {
            System.out.printf("Available Extension: %-25s | Default Version: %-15s | Comment: %s\n", 
                    ext.get("name"), ext.get("default_version"), ext.get("comment"));
        }

        // 3. Flyway Migration History
        System.out.println("\n--- [3] FLYWAY MIGRATION HISTORY ---");
        List<Map<String, Object>> flywayHistory = jdbcTemplate.queryForList(
                "SELECT installed_rank, version, description, type, script, execution_time, success, installed_on FROM flyway_schema_history ORDER BY installed_rank"
        );
        for (Map<String, Object> row : flywayHistory) {
            System.out.printf("Rank: %-3s | Version: %-6s | Description: %-35s | Script: %-45s | Time: %4dms | Success: %s\n",
                    row.get("installed_rank"), row.get("version"), row.get("description"), row.get("script"), row.get("execution_time"), row.get("success"));
        }

        // 4. Tables in public schema
        System.out.println("\n--- [4] ALL PUBLIC TABLES ---");
        List<String> tables = jdbcTemplate.queryForList(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name",
                String.class
        );
        for (String tbl : tables) {
            Long rowCount = jdbcTemplate.queryForObject("SELECT count(*) FROM \"" + tbl + "\"", Long.class);
            System.out.printf("Table: %-30s | Row Count: %d\n", tbl, rowCount);
        }

        // 5. Detailed Column Definitions
        System.out.println("\n--- [5] TABLE COLUMNS & DATA TYPES ---");
        for (String tbl : tables) {
            System.out.println("\nTABLE: " + tbl);
            List<Map<String, Object>> columns = jdbcTemplate.queryForList(
                    "SELECT column_name, data_type, udt_name, is_nullable, column_default " +
                    "FROM information_schema.columns " +
                    "WHERE table_schema = 'public' AND table_name = ? " +
                    "ORDER BY ordinal_position",
                    tbl
            );
            for (Map<String, Object> col : columns) {
                System.out.printf("  - %-30s | type: %-18s | udt: %-15s | nullable: %-5s | default: %s\n",
                        col.get("column_name"), col.get("data_type"), col.get("udt_name"), col.get("is_nullable"), col.get("column_default"));
            }
        }

        // 6. Foreign Keys
        System.out.println("\n--- [6] FOREIGN KEY CONSTRAINTS ---");
        List<Map<String, Object>> foreignKeys = jdbcTemplate.queryForList(
                "SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name, tc.constraint_name " +
                "FROM information_schema.table_constraints AS tc " +
                "JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema " +
                "JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema " +
                "WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public' " +
                "ORDER BY tc.table_name, kcu.column_name"
        );
        for (Map<String, Object> fk : foreignKeys) {
            System.out.printf("FK: %s.%s -> %s.%s (%s)\n",
                    fk.get("table_name"), fk.get("column_name"), fk.get("foreign_table_name"), fk.get("foreign_column_name"), fk.get("constraint_name"));
        }

        // 7. Indexes
        System.out.println("\n--- [7] INDEXES ---");
        List<Map<String, Object>> indexes = jdbcTemplate.queryForList(
                "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname"
        );
        for (Map<String, Object> idx : indexes) {
            System.out.printf("Index on %-25s | Name: %-35s | Def: %s\n",
                    idx.get("tablename"), idx.get("indexname"), idx.get("indexdef"));
        }

        System.out.println("================================================================================");
    }
}
