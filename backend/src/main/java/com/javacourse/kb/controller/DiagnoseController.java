package com.javacourse.kb.controller;

import com.javacourse.kb.model.ErrorCase;
import com.javacourse.kb.service.DiagnoseService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

/** 报错诊断：粘贴 javac / 运行时异常，返回成因与修复建议。 */
@RestController
@RequestMapping("/api/diagnose")
public class DiagnoseController {
    private final DiagnoseService diagnose;

    public DiagnoseController(DiagnoseService diagnose) { this.diagnose = diagnose; }

    public record DiagnoseRequest(String error) {}

    @PostMapping
    public Map<String, Object> run(HttpServletRequest request, @RequestBody DiagnoseRequest body) {
        Long userId = null;
        Object user = request.getAttribute("authUser");
        if (user instanceof com.javacourse.kb.model.UserAccount account) userId = account.getId();
        return Map.of("code", 200, "data", diagnose.diagnose(userId, body.error()));
    }

    @GetMapping("/cases")
    public Map<String, Object> cases() {
        return Map.of("code", 200, "data", diagnose.listCases());
    }

    @GetMapping("/cases/grouped")
    public Map<String, Object> grouped() {
        return Map.of("code", 200, "data", diagnose.groupedCases());
    }

    @PostMapping("/cases")
    public Map<String, Object> create(@RequestBody ErrorCase errorCase) {
        return Map.of("code", 200, "data", diagnose.create(errorCase));
    }
}
