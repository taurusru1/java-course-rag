package com.javacourse.kb.controller;

import com.javacourse.kb.config.RoleGuard;
import com.javacourse.kb.service.TeacherStatsService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

/** 教师端：学情统计。 */
@RestController
@RequestMapping("/api/teacher")
public class TeacherController {
    private final TeacherStatsService stats;

    public TeacherController(TeacherStatsService stats) { this.stats = stats; }

    @GetMapping("/stats")
    public Map<String, Object> overview(HttpServletRequest request, @RequestParam Long courseId) {
        RoleGuard.requireTeacher(request);
        return Map.of("code", 200, "data", stats.overview(courseId));
    }
}
