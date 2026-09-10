package com.cyclovision.ingestion.validation;

import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.dto.ExternalObservationDto;
import org.springframework.stereotype.Component;

@Component
public class CycloneDataValidator {

    public static final double MIN_LATITUDE = -90.0;
    public static final double MAX_LATITUDE = 90.0;
    public static final double MIN_LONGITUDE = -180.0;
    public static final double MAX_LONGITUDE = 180.0;
    public static final double MIN_WIND_SPEED_KPH = 0.0;
    public static final double MAX_WIND_SPEED_KPH = 350.0;
    public static final double MIN_PRESSURE_HPA = 800.0;
    public static final double MAX_PRESSURE_HPA = 1100.0;

    /**
     * Validates cyclone-level metadata.
     * Note: Legitimate historical records may have null/blank basin, name, status, or category;
     * these are accepted and handled safely during persistence.
     */
    public ValidationResult validateCyclone(ExternalCycloneDto cyclone) {
        if (cyclone == null) {
            return ValidationResult.invalid("Cyclone DTO cannot be null");
        }
        if (cyclone.getExternalId() == null || cyclone.getExternalId().trim().isEmpty()) {
            return ValidationResult.invalid("Cyclone externalId is missing or blank");
        }
        if (cyclone.getExternalSource() == null || cyclone.getExternalSource().trim().isEmpty()) {
            return ValidationResult.invalid("Cyclone externalSource is missing or blank");
        }
        return ValidationResult.valid();
    }

    /**
     * Validates observation-level measurements.
     * Rejects physically impossible or malformed coordinates and readings while
     * preserving legitimate real-world records with nullable parameters (wind, pressure, movement).
     */
    public ValidationResult validateObservation(ExternalObservationDto observation) {
        if (observation == null) {
            return ValidationResult.invalid("Observation DTO cannot be null");
        }
        if (observation.getObservedAt() == null) {
            return ValidationResult.invalid("Observation observedAt timestamp is required");
        }
        if (observation.getLatitude() == null) {
            return ValidationResult.invalid("Observation latitude is required");
        }
        if (observation.getLatitude() < MIN_LATITUDE || observation.getLatitude() > MAX_LATITUDE) {
            return ValidationResult.invalid(String.format("Latitude %.2f is outside valid physical range [%.1f, %.1f]",
                    observation.getLatitude(), MIN_LATITUDE, MAX_LATITUDE));
        }
        if (observation.getLongitude() == null) {
            return ValidationResult.invalid("Observation longitude is required");
        }
        if (observation.getLongitude() < MIN_LONGITUDE || observation.getLongitude() > MAX_LONGITUDE) {
            return ValidationResult.invalid(String.format("Longitude %.2f is outside valid physical range [%.1f, %.1f]",
                    observation.getLongitude(), MIN_LONGITUDE, MAX_LONGITUDE));
        }

        // Wind speed validation: nullable; if provided, must be within [0.0, 350.0] km/h
        if (observation.getWindSpeedKph() != null) {
            if (observation.getWindSpeedKph() < MIN_WIND_SPEED_KPH || observation.getWindSpeedKph() > MAX_WIND_SPEED_KPH) {
                return ValidationResult.invalid(String.format("Wind speed %.2f km/h is outside valid range [%.1f, %.1f]",
                        observation.getWindSpeedKph(), MIN_WIND_SPEED_KPH, MAX_WIND_SPEED_KPH));
            }
        }

        // Pressure validation: nullable; if provided, must be within [800.0, 1100.0] hPa
        if (observation.getPressureHpa() != null) {
            if (observation.getPressureHpa() < MIN_PRESSURE_HPA || observation.getPressureHpa() > MAX_PRESSURE_HPA) {
                return ValidationResult.invalid(String.format("Pressure %.2f hPa is outside valid physical range [%.1f, %.1f]",
                        observation.getPressureHpa(), MIN_PRESSURE_HPA, MAX_PRESSURE_HPA));
            }
        }

        // Movement direction validation: nullable; if provided, must be in [0.0, 360.0] degrees
        if (observation.getMovementDirectionDegrees() != null) {
            if (observation.getMovementDirectionDegrees() < 0.0 || observation.getMovementDirectionDegrees() > 360.0) {
                return ValidationResult.invalid(String.format("Movement direction %.2f degrees is outside valid range [0, 360]",
                        observation.getMovementDirectionDegrees()));
            }
        }

        // Movement speed validation: nullable; if provided, must not be negative
        if (observation.getMovementSpeedKph() != null) {
            if (observation.getMovementSpeedKph() < 0.0) {
                return ValidationResult.invalid(String.format("Movement speed %.2f km/h cannot be negative",
                        observation.getMovementSpeedKph()));
            }
        }

        return ValidationResult.valid();
    }
}
