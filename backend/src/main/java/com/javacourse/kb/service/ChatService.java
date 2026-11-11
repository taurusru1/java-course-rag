package com.javacourse.kb.service;
import com.javacourse.kb.client.AiModuleClient;
import java.io.InputStream;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Service;
@Service public class ChatService {
 private final AiModuleClient ai; private final Map<String,String> sessions=new ConcurrentHashMap<>();
 public ChatService(AiModuleClient ai){this.ai=ai;}
 public Map<String,Object> start(String query,Long courseId){String sessionId=UUID.randomUUID().toString();Map response=ai.startQuery(query,courseId,sessionId);String taskId=String.valueOf(response.get("taskId"));sessions.put(sessionId,taskId);return Map.of("code",200,"message","query started","sessionId",sessionId,"taskId",taskId);}
 public Map status(String sessionId){return ai.queryStatus(task(sessionId));}
 public InputStream stream(String sessionId){return ai.queryStream(task(sessionId));}
 public Map sessions(){return ai.querySessions();}
 public Map messages(String sessionId){return ai.querySessionMessages(sessionId);}
 public Map deleteSession(String sessionId){sessions.remove(sessionId);return ai.deleteQuerySession(sessionId);}
 private String task(String id){return sessions.getOrDefault(id,id);}
}
