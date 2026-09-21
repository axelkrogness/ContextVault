import hashlib, math
class EmbeddingService:
    dim=128
    def embed(self,text:str):
        v=[0.0]*self.dim
        for token in text.lower().split():
            h=int(hashlib.sha256(token.encode()).hexdigest(),16); v[h%self.dim]+=1; v[(h>>8)%self.dim]-=.5
        n=math.sqrt(sum(x*x for x in v)) or 1
        return [x/n for x in v]
