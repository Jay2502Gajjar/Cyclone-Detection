package com.cyclovision.controller;

import com.cyclovision.dto.ModelCardDto.ModelCard;
import com.cyclovision.service.ModelCardService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/** Datasets, splits, held-out metrics, the fusion ablation, and what we did not build. */
@RestController
public class ModelCardController {

    private final ModelCardService modelCardService;

    public ModelCardController(ModelCardService modelCardService) {
        this.modelCardService = modelCardService;
    }

    @GetMapping("/api/model-card")
    public ModelCard get() {
        return modelCardService.get();
    }
}
