# This implementation is based on DeBERTa model from:
# Microsoft - https://github.com/microsoft/DeBERTa
# Apache 2.0 License
# 
# 📌 My Study Notes:
#This step is the process where the model transforms words into vectors through embeddings to understand them.
#getattr is used to retrieve attribute values from the config, and if the attribute is not present, it returns a default value.
#BERT uses only the encoder part of the Transformer, and after embedding the data, it performs position encoding to provide positional information.
#After performing position encoding, LayerNorm is applied.

from torch import nn

class BertEmbeddings(nn.Module):
  def __init__(self, config):
    super(BertEmbeddings, self).__init__()
    padding_idx = getattr(config, 'padding_idx', 0)
    self.embedding_size = getattr(config, 'embedding_size', config.hidden_size)
    self.word_embeddings = nn.Embedding(config.vocab_size, self.embedding_size, padding_idx = padding_idx)
    self.position_biased_input = getattr(config, 'position_biased_input', True)
    self.position_embeddings = nn.Embedding(config.max_position_embeddings, self.embedding_size)
     
    if config.type_vocab_size>0:
      self.token_type_embeddings = nn.Embedding(config.type_vocab_size, self.embedding_size)
    
    if self.embedding_size != config.hidden_size:
      self.embed_proj = nn.Linear(self.embedding_size, config.hidden_size, bias=False)
    self.LayerNorm = LayerNorm(config.hidden_size, config.layer_norm_eps)
    self.dropout = StableDropout(config.hidden_dropout_prob)
    self.output_to_half = False
    self.config = config

  def forward(self, input_ids, token_type_ids=None, position_ids=None, mask = None):
    seq_length = input_ids.size(1)
    if position_ids is None:
      position_ids = torch.arange(0, seq_length, dtype=torch.long, device=input_ids.device)
      position_ids = position_ids.unsqueeze(0).expand_as(input_ids)
    if token_type_ids is None:
      token_type_ids = torch.zeros_like(input_ids)

    words_embeddings = self.word_embeddings(input_ids)
    position_embeddings = self.position_embeddings(position_ids.long())

    embeddings = words_embeddings
    if self.config.type_vocab_size>0:
      token_type_embeddings = self.token_type_embeddings(token_type_ids)
      embeddings += token_type_embeddings

    if self.position_biased_input:
      embeddings += position_embeddings

    if self.embedding_size != self.config.hidden_size:
      embeddings = self.embed_proj(embeddings)
    embeddings = MaskedLayerNorm(self.LayerNorm, embeddings, mask)
    embeddings = self.dropout(embeddings)
    return {
        'embeddings': embeddings,
        'position_embeddings': position_embeddings}
    
    