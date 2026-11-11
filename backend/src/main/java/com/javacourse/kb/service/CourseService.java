package com.javacourse.kb.service;

import com.javacourse.kb.model.Chapter;
import com.javacourse.kb.model.Course;
import com.javacourse.kb.model.KnowledgePoint;
import com.javacourse.kb.repository.ChapterRepository;
import com.javacourse.kb.repository.CourseRepository;
import com.javacourse.kb.repository.KnowledgePointRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CourseService {
    private final CourseRepository repository;
    private final ChapterRepository chapters;
    private final KnowledgePointRepository points;

    public CourseService(CourseRepository repository, ChapterRepository chapters, KnowledgePointRepository points) {
        this.repository = repository;
        this.chapters = chapters;
        this.points = points;
    }

    public List<Course> list(){return repository.findAll();}
    public List<Chapter> chapters(Long courseId){return chapters.findByCourseIdOrderByChapterNoAsc(courseId);}
    public List<KnowledgePoint> knowledgePoints(Long courseId){return points.findByCourseIdOrderByIdAsc(courseId);}
    public Course get(Long id){return repository.findById(id).orElseThrow(() -> new IllegalArgumentException("course not found"));}

    @Transactional public Course create(Course course){
        if(course.getName()==null || course.getName().isBlank()) throw new IllegalArgumentException("name is required");
        return repository.save(course);
    }
    @Transactional public Course update(Long id, Course input){
        Course course=get(id);
        if(input.getName()==null || input.getName().isBlank()) throw new IllegalArgumentException("name is required");
        course.setName(input.getName().trim());
        course.setCode(input.getCode());
        course.setDepartment(input.getDepartment());
        course.setSemester(input.getSemester());
        course.setDescription(input.getDescription());
        return repository.save(course);
    }
    @Transactional public void delete(Long id){if(!repository.existsById(id)) throw new IllegalArgumentException("course not found"); repository.deleteById(id);}

    @Transactional public Chapter addChapter(Long courseId, Chapter input){
        get(courseId);
        if(input.getTitle()==null || input.getTitle().isBlank()) throw new IllegalArgumentException("章节标题不能为空");
        input.setCourseId(courseId);
        if(input.getChapterNo()==null){
            int next = chapters.findByCourseIdOrderByChapterNoAsc(courseId).stream()
                .map(Chapter::getChapterNo).filter(n -> n != null).max(Integer::compareTo).orElse(0) + 1;
            input.setChapterNo(next);
        }
        return chapters.save(input);
    }

    @Transactional public Chapter updateChapter(Long id, Chapter input){
        Chapter chapter=chapters.findById(id).orElseThrow(() -> new IllegalArgumentException("chapter not found"));
        if(input.getTitle()==null || input.getTitle().isBlank()) throw new IllegalArgumentException("章节标题不能为空");
        chapter.setTitle(input.getTitle().trim());
        chapter.setChapterNo(input.getChapterNo()==null?chapter.getChapterNo():input.getChapterNo());
        chapter.setSummary(input.getSummary());
        return chapters.save(chapter);
    }

    @Transactional public void deleteChapter(Long id){
        if(!chapters.existsById(id)) throw new IllegalArgumentException("chapter not found");
        chapters.deleteById(id);
    }
}
