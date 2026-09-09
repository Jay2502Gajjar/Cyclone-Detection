package com.cyclovision;

import com.cyclovision.dto.ForecastDto.ForecastResponse;
import com.cyclovision.dto.ForecastDto.IntensityForecast;
import com.cyclovision.dto.ForecastDto.TrackForecast;
import com.cyclovision.dto.ForecastDto.TrackPointDto;
import com.cyclovision.dto.FrameDto.ObservedBlock;
import com.cyclovision.dto.Source;
import com.cyclovision.entity.StormFrame;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;

/** Shared fixtures. Modelled loosely on Fani (2019), a planned demo storm. */
public final class TestFixtures {

    public static final String SID = "2019114N06084";
    public static final OffsetDateTime T0 =
            OffsetDateTime.of(2019, 5, 2, 6, 0, 0, 0, ZoneOffset.UTC);

    private TestFixtures() {
    }

    public static StormFrame frame(OffsetDateTime t, double lat, double lon, Double vmaxKt) {
        StormFrame f = new StormFrame();
        f.setSid(SID);
        f.setObsTime(t);
        f.setLat(lat);
        f.setLon(lon);
        f.setVmaxKt(vmaxKt);
        f.setPressureHpa(950.0);
        f.setCategory("EXTREMELY_SEVERE");
        f.setTranslationSpeedKt(9.0);
        f.setHeadingDeg(15.0);
        f.setDistToCoastKm(310.0);
        return f;
    }

    /** A 3-hourly sequence spanning {@code before} points up to T0 and {@code after} beyond it. */
    public static List<StormFrame> sequenceAround(OffsetDateTime centre, int before, int after) {
        List<StormFrame> frames = new ArrayList<>();
        for (int i = -before; i <= after; i++) {
            frames.add(frame(centre.plusHours(3L * i), 17.0 + i * 0.2, 85.0 + i * 0.1,
                    120.0 + i));
        }
        return frames;
    }

    public static ForecastResponse forecastWithTrack(OffsetDateTime issuedFor,
            double lat24, double lon24, double coneP67Km, double coneP90Km,
            Double predictedVmax24hKt, Double riProbability) {

        TrackPointDto p24 = new TrackPointDto(24, lat24, lon24, coneP67Km, coneP90Km,
                predictedVmax24hKt);
        TrackForecast track = new TrackForecast(List.of(p24),
                Source.demoData("track_cliper", "phase0"),
                Source.demoData("track_cone", "phase0"),
                "Phase 0 placeholder: cone radii are not yet calibrated.");

        IntensityForecast intensity = new IntensityForecast(8.0, predictedVmax24hKt,
                "INTENSIFYING", 0.5, riProbability, 0.05, List.of(),
                Source.demoData("dvmax_ri", "phase0"));

        ObservedBlock current = new ObservedBlock(17.2, 85.1, 125.0, 936.0,
                "EXTREMELY_SEVERE", 310.0, Source.observed());

        return new ForecastResponse(SID, issuedFor, "phase0", current, null, null,
                intensity, track, null, null, null, null, false, "live");
    }
}
