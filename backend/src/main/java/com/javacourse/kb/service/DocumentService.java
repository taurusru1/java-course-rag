package com.javacourse.kb.service;

import com.javacourse.kb.client.AiModuleClient;
import com.javacourse.kb.model.*;
import com.javacourse.kb.repository.DocumentRepository;
import java.util.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
public class DocumentService {
    private final DocumentRepository repository; private final CourseService courses; private final StorageService storage; private final AiModuleClient ai;
    public DocumentService(DocumentRepository r,CourseService c,StorageService s,AiModuleClient a){repository=r;courses=c;storage=s;ai=a;}
    @Transactional public Document upload(MultipartFile file,Long courseId,String docType) throws Exception {
        Course course=courses.get(courseId); String objectName="documents/"+UUID.randomUUID()+"-"+file.getOriginalFilename();
        String url=storage.upload(objectName,file.getInputStream(),file.getSize(),file.getContentType());
        Document d=new Document();d.setCourse(course);d.setFileName(file.getOriginalFilename());d.setFileSize(file.getSize());d.setDocType(docType);d.setStatus("processing");d=repository.save(d);
        Map response=ai.startImport(url,courseId,course.getName(),docType);d.setTaskId(String.valueOf(response.get("taskId")));return repository.save(d);
    }
    public List<Document> list(Long courseId){return courseId==null?repository.findAll():repository.findByCourseIdOrderByCreatedAtDesc(courseId);}
    @Transactional public void delete(Long id){
        if(!repository.existsById(id)) throw new IllegalArgumentException("document not found");
        repository.deleteById(id);
    }
    public Map<String,Object> get(Long id){Document d=repository.findById(id).orElseThrow(()->new IllegalArgumentException("document not found"));Map<String,Object> result=new LinkedHashMap<>();result.put("id",d.getId());result.put("fileName",d.getFileName());result.put("status",d.getStatus());result.put("taskId",d.getTaskId());if(d.getTaskId()!=null)result.putAll(ai.importStatus(d.getTaskId()));return result;}
}
