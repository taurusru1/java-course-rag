package com.javacourse.kb.controller;

import com.javacourse.kb.service.TeacherDashboardService;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/teacher")
public class TeacherDashboardController {
    private final TeacherDashboardService service;
    public TeacherDashboardController(TeacherDashboardService service) { this.service = service; }
    @GetMapping("/dashboard") public Map<String, Object> dashboard() {
        return Map.of("code", 200, "data", service.summary());
    }
}
