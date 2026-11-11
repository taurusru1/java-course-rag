package com.javacourse.kb.controller;
import com.javacourse.kb.service.ChatService; import java.util.Map; import org.springframework.http.*; import org.springframework.web.bind.annotation.*; import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;
@RestController @RequestMapping("/api/chat") public class ChatController {
 private final ChatService service; public ChatController(ChatService s){service=s;}
 public record ChatRequest(String query,Long courseId,String scope){}
 @PostMapping public Map start(@RequestBody ChatRequest request){if(request.query()==null||request.query().isBlank())throw new IllegalArgumentException("query is required");return service.start(request.query(),request.courseId(),request.scope());}
 @GetMapping("/{sessionId}") public Map status(@PathVariable String sessionId){Map data=service.status(sessionId);return Map.of("code",200,"answer",data.getOrDefault("answer",""),"sources",data.getOrDefault("sources",java.util.List.of()),"status",data.getOrDefault("status",""));}
 @GetMapping(value="/{sessionId}/stream",produces=MediaType.TEXT_EVENT_STREAM_VALUE) public ResponseEntity<StreamingResponseBody> stream(@PathVariable String sessionId){return ResponseEntity.ok().contentType(MediaType.TEXT_EVENT_STREAM).body(out->{try(var in=service.stream(sessionId)){in.transferTo(out);}});}
 @GetMapping("/sessions") public Map sessions(){return service.sessions();}
 @GetMapping("/sessions/{sessionId}/messages") public Map messages(@PathVariable String sessionId){return service.messages(sessionId);}
 @DeleteMapping("/sessions/{sessionId}") public Map deleteSession(@PathVariable String sessionId){return service.deleteSession(sessionId);}
}
