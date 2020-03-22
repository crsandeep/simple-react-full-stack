import React from 'react';
import { shallow, mount } from 'enzyme';
import HeaderComp from '../src/client/components/HeaderComp';
import { BrowserRouter as Router } from 'react-router-dom';


describe('<HeaderComp/>', () => {
    it('Positive case', () => {
      expect(2 + 2).toBe(4);
    });

    it('Render <HeaderComp> without links', () => {
        const wrapper = shallow(<HeaderComp />);
        expect(wrapper).toHaveLength(1);
        
        expect(wrapper.find('Navbar')).toHaveLength(1);
        expect(wrapper.find('Form')).toHaveLength(1);
        expect(wrapper.find('Button')).toHaveLength(1);

        expect(wrapper.find('Nav.Link')).toHaveLength(0);
    });
    
    it('Render <HeaderComp> with links', () => {
        const linkMap = new Map([
            ['Home', '/home'],
            ['Space', '/space'],
            ['Item', '/item'],
        ]);

        const wrapper = mount(<Router><HeaderComp linkMap={linkMap}/></Router>);
        expect(wrapper).toHaveLength(1);
        
        expect(wrapper.find('Navbar')).toHaveLength(1);
        expect(wrapper.find('Form')).toHaveLength(1);
        expect(wrapper.find('Button')).toHaveLength(1);

        //links = 3
        expect(wrapper.find('a.nav-link')).toHaveLength(3);

        //check links
        expect(wrapper.find('a.nav-link').first().props().href).toEqual('/home');
        expect(wrapper.find('a.nav-link').last().props().href).toEqual('/item');

    });

});