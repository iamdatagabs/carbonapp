package br.com.carbonapp.api.field;
import java.time.Instant;
import java.util.UUID;
import jakarta.persistence.*;
@Entity @Table(name="field_records")
public class FieldRecord {
 @Id @GeneratedValue private UUID id;
 @Column(nullable=false,length=80) private String projectCode;
 @Column(nullable=false,length=80) private String pointCode;
 @Column(nullable=false,length=1) private String depthCode;
 @Column(length=2000) private String notes;
 @Column(nullable=false,updatable=false) private Instant createdAt;
 protected FieldRecord(){}
 public FieldRecord(String projectCode,String pointCode,String depthCode,String notes){this.projectCode=projectCode;this.pointCode=pointCode;this.depthCode=depthCode;this.notes=notes;}
 @PrePersist void onCreate(){createdAt=Instant.now();}
 public UUID getId(){return id;} public String getProjectCode(){return projectCode;} public String getPointCode(){return pointCode;}
 public String getDepthCode(){return depthCode;} public String getNotes(){return notes;} public Instant getCreatedAt(){return createdAt;}
}
