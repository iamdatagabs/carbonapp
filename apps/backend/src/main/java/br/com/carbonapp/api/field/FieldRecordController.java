package br.com.carbonapp.api.field;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;
@RestController @RequestMapping("/api/v1/field-records")
public class FieldRecordController {
 private final FieldRecordRepository repository;
 public FieldRecordController(FieldRecordRepository repository){this.repository=repository;}
 @GetMapping public List<FieldRecord> list(){return repository.findAll();}
 @PostMapping @ResponseStatus(HttpStatus.CREATED)
 public FieldRecord create(@Valid @RequestBody FieldRecordRequest request){
  return repository.save(new FieldRecord(request.projectCode(),request.pointCode(),request.depthCode(),request.notes()));
 }
}
