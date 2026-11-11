package com.javacourse.kb.service;

import com.javacourse.kb.model.Course;
import com.javacourse.kb.repository.CourseRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CourseService {
    private final CourseRepository repository;
    public CourseService(CourseRepository repository){this.repository=repository;}
    public List<Course> list(){return repository.findAll();}
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
}
