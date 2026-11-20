package br.com.carbonapp.api;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;
@SpringBootTest @AutoConfigureMockMvc
class MetadataControllerTest {
 @Autowired MockMvc mvc; @Autowired ObjectMapper mapper;
 @Test void returnsNineAuthoritativeDepthIntervals() throws Exception {
  String body=mvc.perform(get("/api/v1/metadata/depths")).andExpect(status().isOk()).andReturn().getResponse().getContentAsString();
  JsonNode json=mapper.readTree(body); assertThat(json).hasSize(9); assertThat(json.get(8).get("bottomCm").asInt()).isEqualTo(200);
 }
}
