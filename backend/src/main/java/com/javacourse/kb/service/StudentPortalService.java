package com.javacourse.kb.service;
import com.javacourse.kb.model.*; import com.javacourse.kb.repository.*; import java.util.*;
import org.springframework.stereotype.Service; import org.springframework.transaction.annotation.Transactional;
@Service
public class StudentPortalService {
 private final StudentRepository students; private final KnowledgeCategoryRepository categories; private final CampusNoticeRepository notices;
 private final ChatHistoryRepository histories; private final StudentFavoriteRepository favorites;
 public StudentPortalService(StudentRepository s,KnowledgeCategoryRepository c,CampusNoticeRepository n,ChatHistoryRepository h,StudentFavoriteRepository f){students=s;categories=c;notices=n;histories=h;favorites=f;}
 public Student profile(Long id){return students.findById(id).orElseThrow(()->new IllegalArgumentException("student not found"));}
 @Transactional public Student updateProfile(Long id,Map<String,String> body){Student s=profile(id); if(body.containsKey("name"))s.setName(body.get("name")); if(body.containsKey("email"))s.setEmail(body.get("email")); return students.save(s);}
 public List<KnowledgeCategory> categories(){return categories.findByEnabledTrueOrderBySortOrderAsc();}
 public List<CampusNotice> notices(String category){return category==null||category.isBlank()?notices.findAllByOrderByPublishedAtDesc():notices.findByCategoryOrderByPublishedAtDesc(category);}
 public List<ChatHistory> histories(Long studentId,String category){profile(studentId); return category==null||category.isBlank()?histories.findByStudentIdOrderByCreatedAtDesc(studentId):histories.findByStudentIdAndCategoryOrderByCreatedAtDesc(studentId,category);}
 @Transactional public ChatHistory saveHistory(Long studentId,ChatHistory item){profile(studentId); item.setStudentId(studentId); if(item.getQuestion()==null||item.getQuestion().isBlank())throw new IllegalArgumentException("question is required"); return histories.save(item);}
 public List<StudentFavorite> favorites(Long studentId){profile(studentId);return favorites.findByStudentIdOrderByCreatedAtDesc(studentId);}
 @Transactional public StudentFavorite addFavorite(Long studentId,StudentFavorite item){profile(studentId);item.setStudentId(studentId);if(item.getTitle()==null||item.getTitle().isBlank())throw new IllegalArgumentException("title is required");if(item.getItemType()==null)item.setItemType("问答");return favorites.save(item);}
 @Transactional public void removeFavorite(Long studentId,Long id){StudentFavorite item=favorites.findById(id).orElseThrow(()->new IllegalArgumentException("favorite not found"));if(!item.getStudentId().equals(studentId))throw new IllegalArgumentException("favorite not found");favorites.delete(item);}
 public Map<String,Long> summary(Long studentId){return Map.of("historyCount",(long)histories.findByStudentIdOrderByCreatedAtDesc(studentId).size(),"favoriteCount",(long)favorites.findByStudentIdOrderByCreatedAtDesc(studentId).size(),"categoryCount",(long)categories.findByEnabledTrueOrderBySortOrderAsc().size());}
}
