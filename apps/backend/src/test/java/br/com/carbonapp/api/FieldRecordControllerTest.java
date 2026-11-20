package br.com.carbonapp.api;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
@SpringBootTest @AutoConfigureMockMvc
class FieldRecordControllerTest {
 @Autowired MockMvc mvc;
 @Test void acceptsValidFieldRecord() throws Exception {
  mvc.perform(post("/api/v1/field-records").contentType(MediaType.APPLICATION_JSON).content("{\"projectCode\":\"DEMO\",\"pointCode\":\"P01\",\"depthCode\":\"A\",\"notes\":\"MVP test\"}")).andExpect(status().isCreated());
 }
 @Test void rejectsUnknownDepthCode() throws Exception {
  mvc.perform(post("/api/v1/field-records").contentType(MediaType.APPLICATION_JSON).content("{\"projectCode\":\"DEMO\",\"pointCode\":\"P01\",\"depthCode\":\"Z\"}")).andExpect(status().isBadRequest());
 }
}
