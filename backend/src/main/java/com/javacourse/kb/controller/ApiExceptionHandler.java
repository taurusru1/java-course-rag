package com.javacourse.kb.controller;
import com.javacourse.kb.client.AiModuleClient.AiUnavailableException; import com.javacourse.kb.config.ForbiddenException; import java.util.Map; import org.springframework.http.*; import org.springframework.web.bind.annotation.*;
@RestControllerAdvice public class ApiExceptionHandler {
 @ExceptionHandler(IllegalArgumentException.class) ResponseEntity<Map<String,Object>> bad(IllegalArgumentException e){HttpStatus s=e.getMessage().contains("not found")?HttpStatus.NOT_FOUND:HttpStatus.BAD_REQUEST;return ResponseEntity.status(s).body(Map.of("code",s.value(),"message",e.getMessage()));}
 @ExceptionHandler(SecurityException.class) ResponseEntity<Map<String,Object>> unauthorized(SecurityException e){return ResponseEntity.status(401).body(Map.of("code",401,"message",e.getMessage()));}
 @ExceptionHandler(ForbiddenException.class) ResponseEntity<Map<String,Object>> forbidden(ForbiddenException e){return ResponseEntity.status(403).body(Map.of("code",403,"message",e.getMessage()));}
 @ExceptionHandler(AiUnavailableException.class) ResponseEntity<Map<String,Object>> ai(AiUnavailableException e){return ResponseEntity.status(503).body(Map.of("code",503,"message",e.getMessage()));}
}
