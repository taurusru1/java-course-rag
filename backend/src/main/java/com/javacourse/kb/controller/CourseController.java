package com.javacourse.kb.controller;
import com.javacourse.kb.model.Course; import com.javacourse.kb.service.CourseService; import java.util.Map;
import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api/courses") public class CourseController {
 private final CourseService service; public CourseController(CourseService s){service=s;}
 @GetMapping public Map list(){return Map.of("code",200,"data",service.list());}
 @PostMapping public Map create(@RequestBody Course course){Course saved=service.create(course);return Map.of("code",200,"message","course created","courseId",saved.getId());}
 @GetMapping("/{id}") public Map get(@PathVariable Long id){return Map.of("code",200,"data",service.get(id));}
 @PutMapping("/{id}") public Map update(@PathVariable Long id,@RequestBody Course course){return Map.of("code",200,"message","course updated","data",service.update(id,course));}
 @DeleteMapping("/{id}") public Map delete(@PathVariable Long id){service.delete(id);return Map.of("code",200,"message","course deleted");}
}
