package com.javacourse.kb.controller;
import com.javacourse.kb.model.*; import com.javacourse.kb.service.StudentPortalService; import java.util.Map;
import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api/student")
public class StudentPortalController {
 private final StudentPortalService service; public StudentPortalController(StudentPortalService s){service=s;}
 @GetMapping("/{id}/profile") public Map<String,Object> profile(@PathVariable Long id){return Map.of("code",200,"data",service.profile(id));}
 @PutMapping("/{id}/profile") public Map<String,Object> update(@PathVariable Long id,@RequestBody Map<String,String> body){return Map.of("code",200,"data",service.updateProfile(id,body),"message","profile updated");}
 @GetMapping("/{id}/summary") public Map<String,Object> summary(@PathVariable Long id){return Map.of("code",200,"data",service.summary(id));}
 @GetMapping("/{id}/history") public Map<String,Object> history(@PathVariable Long id,@RequestParam(required=false) String category){return Map.of("code",200,"data",service.histories(id,category));}
 @PostMapping("/{id}/history") public Map<String,Object> saveHistory(@PathVariable Long id,@RequestBody ChatHistory item){return Map.of("code",200,"data",service.saveHistory(id,item));}
 @GetMapping("/{id}/favorites") public Map<String,Object> favorites(@PathVariable Long id){return Map.of("code",200,"data",service.favorites(id));}
 @PostMapping("/{id}/favorites") public Map<String,Object> addFavorite(@PathVariable Long id,@RequestBody StudentFavorite item){return Map.of("code",200,"data",service.addFavorite(id,item));}
 @DeleteMapping("/{studentId}/favorites/{id}") public Map<String,Object> removeFavorite(@PathVariable Long studentId,@PathVariable Long id){service.removeFavorite(studentId,id);return Map.of("code",200,"message","favorite removed");}
}
