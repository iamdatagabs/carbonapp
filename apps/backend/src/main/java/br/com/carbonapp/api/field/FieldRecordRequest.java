package br.com.carbonapp.api.field;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
public record FieldRecordRequest(@NotBlank @Size(max=80) String projectCode,@NotBlank @Size(max=80) String pointCode,@NotBlank @Pattern(regexp="[A-I]") String depthCode,@Size(max=2000) String notes) {}
