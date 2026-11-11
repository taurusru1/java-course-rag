package com.javacourse.kb.controller;
import com.javacourse.kb.model.Document; import com.javacourse.kb.service.DocumentService; import java.util.Map;
import org.springframework.web.bind.annotation.*; import org.springframework.web.multipart.MultipartFile;
@RestController @RequestMapping("/api/documents") public class DocumentController {
 private final DocumentService service; public DocumentController(DocumentService s){service=s;}
 @PostMapping public Map upload(@RequestParam MultipartFile file,@RequestParam Long courseId,@RequestParam(defaultValue="other") String docType)throws Exception{Document d=service.upload(file,courseId,docType);return Map.of("code",200,"documentId",d.getId(),"taskId",d.getTaskId());}
 @GetMapping public Map list(@RequestParam(required=false) Long courseId){return Map.of("code",200,"data",service.list(courseId));}
 @GetMapping("/{id}") public Map get(@PathVariable Long id){return service.get(id);}
 @DeleteMapping("/{id}") public Map delete(@PathVariable Long id){service.delete(id);return Map.of("code",200,"message","document deleted");}
}
