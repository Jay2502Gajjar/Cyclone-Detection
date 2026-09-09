package com.cyclovision.config;

import java.nio.file.Path;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Serves satellite frames and Grad-CAM overlays from the filesystem.
 *
 * <p>Images are files; the database stores paths only. Putting multi-megabyte rasters in
 * Postgres would slow every timeline query for no benefit.
 */
@Configuration
public class MediaConfig implements WebMvcConfigurer {

    private final String mediaDir;

    public MediaConfig(@Value("${cyclovision.media-dir:../data}") String mediaDir) {
        this.mediaDir = mediaDir;
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        String location = Path.of(mediaDir).toAbsolutePath().normalize().toUri().toString();
        registry.addResourceHandler("/media/**").addResourceLocations(location);
    }
}
