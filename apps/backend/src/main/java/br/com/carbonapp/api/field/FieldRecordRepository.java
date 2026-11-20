package br.com.carbonapp.api.field;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
public interface FieldRecordRepository extends JpaRepository<FieldRecord,UUID> {}
