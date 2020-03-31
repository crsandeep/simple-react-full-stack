const request = require("supertest");
const express = require('express');
import { Container } from 'typedi';

describe('POST /item', () => {
  let expressApp = null;

  beforeAll(async (done)=> {
    expressApp = await require('../../src/server/app');
    done();
  });

  afterAll(async () => {
    const conn = Container.get('mongooseConn');
    const itemModel = Container.get('itemModel');

    // console.log('Finished2');
    // await itemModel.counterReset('itemId', function(err) {
    //   console.log(`The counter was reset ${err}`)
      // Now the counter is 0
    // });
    // itemModel._resetCount().then(val => console.log(`The counter was reset to ${val}`));
    // console.log('Finished 3');
    await conn.db.dropCollection(
      "items",
      // function(err, result) {
      //   console.log("Collection droped");
      // }
    );
    await conn.close();
    done();
  });

  it('positive case', async () => {
    const submitValues = {
      "itemId": null,
      "spaceId": 1,
      "name": "Item Name - 123",
      "tags": "business",
      "category": "clothes",
      "colorCode": "yellow",
      "description": "Item description - 123",
      "imgPath": null,
      "reminderDtm": "2020-03-27T03:17:09",
      "reminderComplete": null
    };

    const expectValues = {
      "isSuccess": true,
      "payload": {
          "itemId": 2,
          "spaceId": 1,
          "name": "Item Name - 123",
          "tags": "business",
          "category": "clothes",
          "colorCode": "yellow",
          "description": "Item description - 123",
          "imgPath": null,
          "reminderDtm": "2020-03-26T19:17:09.000Z",
          "reminderComplete": false
      },
      "message": null
    }
      
    const response = await request(expressApp)
      .post('/api/item')
      .send(submitValues)
    expect(response.statusCode).toEqual(201)
    expect(response.body).toHaveProperty('isSuccess')
    expect(response.body).toHaveProperty('message')
    expect(response.body).toHaveProperty('payload')

    // expect(response.body).toEqual(expectValues)

      // const response = await request(expressApp).get('/api/item/4')
      // expect(response.body).toEqual(expectValues);
      // expect(response.statusCode).toBe(200);
  });
    
});