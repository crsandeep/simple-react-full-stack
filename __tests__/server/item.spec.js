const request = require("supertest");
const express = require('express');
import { Container } from 'typedi';



describe('GET /item', () => {
  let expressApp = null;

  beforeAll(async (done)=> {
      expressApp = express();
      await require('../../src/server/loaders').default({ expressApp })
      done();
  });

  afterAll(async () => {
    // const conn = Container.get('mongooseConn');
    // await conn.close();
    done();
  });

    it('positive case', () => {
      expect(2 + 2).toBe(4);
    });

    it('positive case', async () => {
        const expectValues = {result:{itemId:21}};
        
        const response = await request(expressApp)
                              .get('/api/item/25')
        expect(response.body).toEqual(expectValues);
        expect(response.statusCode).toBe(200);
    });
    
});