import React from 'react';
import { shallow } from 'enzyme';
import AppTest from '../src/client/components/AppTest';
import renderer from 'react-test-renderer'


describe('<AppTest/>', () => {
    it('positive case', () => {
      expect(2 + 2).toBe(4);
    });

    // it('render <AppTest>', () => {
    //     const wrapper = shallow(<AppTest />);
    //     expect(wrapper).toHaveLength(1);

    //     // const tree = renderer.create(<AppTest />).toJSON()
    //     // expect(tree).toMatchSnapshot()
    // });

    // it('render <sub components>', () => {
    //     const wrapper = shallow(<AppTest />);
        
    //     expect(wrapper.find('div')).toHaveLength(1);
    //     expect(wrapper.find('h1')).toHaveLength(1);
    //     expect(wrapper.find('img')).toHaveLength(1);
    // });
    

    // it('initial render display text', () => {
    //     const wrapper = shallow(<AppTest />);

    //     const text = wrapper.find('p').text();
    //     expect(text).toEqual('testing');

    //     expect(wrapper.state('username')).toBeNull();

    //     const h1Text = wrapper.find('h1').text();
    //     expect(h1Text).toEqual('Loading.. please wait!');

    //     expect(wrapper.contains('input')).toBe(false)
        
    // });
    
    // it('render display text after click', () => {
    //     const wrapper = shallow(<AppTest />);
    //     //click btn
    //     wrapper.find('button').last().simulate('click');

    //     //chec state
    //     expect(wrapper.state('username')).toEqual('abc');
    //     expect(wrapper.state('input')).toEqual('');

    //     //text show
    //     const h1Text = wrapper.find('h1').text();
    //     expect(h1Text).toEqual('Hello abc');
        
    //     //input show
    //     expect(wrapper.find('input')).toHaveLength(1);
    // });
    
    
    // it('render display text after enter value', () => {
    //     const wrapper = shallow(<AppTest/>);

    //     wrapper.find('button').last().simulate('click');

    //     //check state
    //     expect(wrapper.find('input')).toHaveLength(1);

    //     //enter text
    //     const inputComp = wrapper.find('#txtField');
    //     inputComp.simulate('change', {target: {value: 'Test'}});
        
    //     //check state
    //     expect(wrapper.state('input')).toEqual('Test');
    // });

    // it('render correctly if showMsg is true', () => {
    //     const tree = renderer.create(<AppTest showMsg={true}/>).toJSON()
    //     expect(tree).toMatchSnapshot()
    // });

    
    // it('render correctly if showMsg is false', () => {
    //     const tree = renderer.create(<AppTest showMsg={false}/>).toJSON()
    //     expect(tree).toMatchSnapshot()
    // });
});