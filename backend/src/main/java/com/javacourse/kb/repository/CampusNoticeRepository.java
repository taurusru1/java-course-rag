package com.javacourse.kb.repository;
import com.javacourse.kb.model.CampusNotice; import java.util.List; import org.springframework.data.jpa.repository.JpaRepository;
public interface CampusNoticeRepository extends JpaRepository<CampusNotice,Long>{List<CampusNotice> findAllByOrderByPublishedAtDesc(); List<CampusNotice> findByCategoryOrderByPublishedAtDesc(String category);}
