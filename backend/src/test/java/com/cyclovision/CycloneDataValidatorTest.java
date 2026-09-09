package com.cyclovision;

import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.dto.ExternalObservationDto;
import com.cyclovision.ingestion.validation.CycloneDataValidator;
import com.cyclovision.ingestion.validation.ValidationResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.*;

class CycloneDataValidatorTest {

    private CycloneDataValidator validator;

    @BeforeEach
    void setUp() {
        validator = new CycloneDataValidator();
    }

    private ExternalObservationDto createValidObservation() {
        ExternalObservationDto obs = new ExternalObservationDto();
        obs.setExternalCycloneId("1884152N17091");
        obs.setSourceRecordId("1884152N17091-1884-06-01T00:00:00Z");
        obs.setSource("IBTrACS");
        obs.setObservedAt(Instant.parse("1884-06-01T00:00:00Z"));
        obs.setLatitude(17.5);
        obs.setLongitude(90.2);
        obs.setWindSpeedKph(65.0);
        obs.setPressureHpa(998.0);
        obs.setMovementSpeedKph(15.0);
        obs.setMovementDirectionDegrees(45.0);
        return obs;
    }

    private ExternalCycloneDto createValidCyclone() {
        ExternalCycloneDto cyclone = new ExternalCycloneDto();
        cyclone.setExternalId("1884152N17091");
        cyclone.setExternalSource("IBTrACS");
        cyclone.setName("BIPARJOY");
        cyclone.setBasin("NI");
        cyclone.setStatus("HISTORICAL");
        cyclone.setCurrentCategory("Very Severe Cyclonic Storm");
        return cyclone;
    }

    @Test
    @DisplayName("Valid observation should be accepted")
    void testValidObservationAccepted() {
        ExternalObservationDto obs = createValidObservation();
        ValidationResult result = validator.validateObservation(obs);
        assertTrue(result.isValid(), "Expected observation to be valid");
        assertNull(result.getReason());
    }

    @Test
    @DisplayName("Observation with null wind speed should be accepted")
    void testNullWindSpeedAccepted() {
        ExternalObservationDto obs = createValidObservation();
        obs.setWindSpeedKph(null);
        ValidationResult result = validator.validateObservation(obs);
        assertTrue(result.isValid(), "Null wind speed should be accepted for historical records");
    }

    @Test
    @DisplayName("Observation with null pressure should be accepted")
    void testNullPressureAccepted() {
        ExternalObservationDto obs = createValidObservation();
        obs.setPressureHpa(null);
        ValidationResult result = validator.validateObservation(obs);
        assertTrue(result.isValid(), "Null pressure should be accepted for historical records");
    }

    @Test
    @DisplayName("Observation with null movement speed/direction should be accepted")
    void testNullMovementAccepted() {
        ExternalObservationDto obs = createValidObservation();
        obs.setMovementSpeedKph(null);
        obs.setMovementDirectionDegrees(null);
        ValidationResult result = validator.validateObservation(obs);
        assertTrue(result.isValid(), "Null movement parameters should be accepted");
    }

    @ParameterizedTest
    @ValueSource(doubles = {-90.1, 90.1, -120.0, 150.0})
    @DisplayName("Observation with invalid latitude should be rejected")
    void testInvalidLatitudeRejected(double lat) {
        ExternalObservationDto obs = createValidObservation();
        obs.setLatitude(lat);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid(), "Latitude " + lat + " must be rejected");
        assertTrue(result.getReason().contains("Latitude"));
    }

    @Test
    @DisplayName("Observation with null latitude should be rejected")
    void testNullLatitudeRejected() {
        ExternalObservationDto obs = createValidObservation();
        obs.setLatitude(null);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("latitude is required"));
    }

    @ParameterizedTest
    @ValueSource(doubles = {-180.1, 180.1, -200.0, 360.0})
    @DisplayName("Observation with invalid longitude should be rejected")
    void testInvalidLongitudeRejected(double lon) {
        ExternalObservationDto obs = createValidObservation();
        obs.setLongitude(lon);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid(), "Longitude " + lon + " must be rejected");
        assertTrue(result.getReason().contains("Longitude"));
    }

    @Test
    @DisplayName("Observation with null longitude should be rejected")
    void testNullLongitudeRejected() {
        ExternalObservationDto obs = createValidObservation();
        obs.setLongitude(null);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("longitude is required"));
    }

    @Test
    @DisplayName("Observation with negative wind speed should be rejected")
    void testNegativeWindSpeedRejected() {
        ExternalObservationDto obs = createValidObservation();
        obs.setWindSpeedKph(-5.0);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("Wind speed"));
    }

    @Test
    @DisplayName("Observation with wind speed above 350 km/h should be rejected")
    void testExcessiveWindSpeedRejected() {
        ExternalObservationDto obs = createValidObservation();
        obs.setWindSpeedKph(351.0);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("Wind speed"));
    }

    @ParameterizedTest
    @ValueSource(doubles = {799.9, 500.0, -10.0, 1100.1, 1500.0})
    @DisplayName("Observation with pressure outside [800, 1100] hPa should be rejected")
    void testInvalidPressureRejected(double pressure) {
        ExternalObservationDto obs = createValidObservation();
        obs.setPressureHpa(pressure);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid(), "Pressure " + pressure + " must be rejected");
        assertTrue(result.getReason().contains("Pressure"));
    }

    @Test
    @DisplayName("Observation with missing timestamp should be rejected")
    void testMissingTimestampRejected() {
        ExternalObservationDto obs = createValidObservation();
        obs.setObservedAt(null);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("observedAt timestamp is required"));
    }

    @Test
    @DisplayName("Observation with negative movement speed should be rejected")
    void testNegativeMovementSpeedRejected() {
        ExternalObservationDto obs = createValidObservation();
        obs.setMovementSpeedKph(-1.0);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("Movement speed"));
    }

    @ParameterizedTest
    @ValueSource(doubles = {-0.1, 360.1, 400.0})
    @DisplayName("Observation with movement direction outside [0, 360] degrees should be rejected")
    void testInvalidMovementDirectionRejected(double dir) {
        ExternalObservationDto obs = createValidObservation();
        obs.setMovementDirectionDegrees(dir);
        ValidationResult result = validator.validateObservation(obs);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("Movement direction"));
    }

    @Test
    @DisplayName("Valid IBTrACS cyclone with nullable fields should be accepted")
    void testValidCycloneWithNullableFieldsAccepted() {
        ExternalCycloneDto cyclone = new ExternalCycloneDto();
        cyclone.setExternalId("1884152N17091");
        cyclone.setExternalSource("IBTrACS");
        cyclone.setName(null);      // null name accepted
        cyclone.setBasin(null);     // null basin accepted
        cyclone.setStatus(null);    // null status accepted
        cyclone.setCurrentCategory(null); // null category accepted

        ValidationResult result = validator.validateCyclone(cyclone);
        assertTrue(result.isValid(), "Cyclone with nullable fields must be accepted");
    }

    @Test
    @DisplayName("Cyclone with missing externalId should be rejected")
    void testCycloneMissingExternalIdRejected() {
        ExternalCycloneDto cyclone = createValidCyclone();
        cyclone.setExternalId("  ");
        ValidationResult result = validator.validateCyclone(cyclone);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("externalId is missing or blank"));
    }

    @Test
    @DisplayName("Cyclone with missing externalSource should be rejected")
    void testCycloneMissingExternalSourceRejected() {
        ExternalCycloneDto cyclone = createValidCyclone();
        cyclone.setExternalSource("");
        ValidationResult result = validator.validateCyclone(cyclone);
        assertFalse(result.isValid());
        assertTrue(result.getReason().contains("externalSource is missing or blank"));
    }
}
