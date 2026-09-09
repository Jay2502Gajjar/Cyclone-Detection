package com.cyclovision.client;

/** The AI service timed out, refused the connection, or returned an error status. */
public class AiServiceUnavailableException extends RuntimeException {

    public AiServiceUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }

    public AiServiceUnavailableException(String message) {
        super(message);
    }
}
