package com.cyclovision.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * The single error envelope for every non-2xx response.
 *
 * <p>Codes: {@code STORM_NOT_FOUND}, {@code FRAME_NOT_FOUND},
 * {@code AI_SERVICE_UNAVAILABLE}, {@code TEMPORAL_MASK_VIOLATION},
 * {@code INVALID_TIME}, {@code MODEL_NOT_LOADED}, {@code INTERNAL_ERROR}.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ApiError(String code, String message, String detail) {

    public static ApiError of(String code, String message) {
        return new ApiError(code, message, null);
    }
}
