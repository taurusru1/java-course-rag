package com.javacourse.kb.controller;
import com.javacourse.kb.service.StudentPortalService; import java.util.Map; import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api/portal")
public class PortalContentController {
 private final StudentPortalService service; public PortalContentController(StudentPortalService s){service=s;}
 @GetMapping("/categories") public Map<String,Object> categories(){return Map.of("code",200,"data",service.categories());}
 @GetMapping("/notices") public Map<String,Object> notices(@RequestParam(required=false) String category){return Map.of("code",200,"data",service.notices(category));}
}
